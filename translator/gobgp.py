"""A translator interface for GoBGP (https://github.com/osrg/gobgp)."""

import logging
from enum import Enum
from ipaddress import IPv4Interface, IPv6Interface, ip_network
from typing import Annotated

import attribute_pb2
import gobgp_pb2
import gobgp_pb2_grpc
import grpc
import redis
from exceptions import ASNError
from google.protobuf.any_pb2 import Any
from shared import asn_is_valid, strip_distinguished_prefix

_TIMEOUT_SECONDS = 1000
PREFIX_CACHE_TIMEOUT_SECONDS = 60
DEFAULT_ASN = 65400
DEFAULT_COMMUNITY = 666
DEFAULT_V4_NEXTHOP = "192.0.2.199"
DEFAULT_V6_NEXTHOP = "100::1"
MAX_SMALL_ASN = 2**16
MAX_SMALL_COMM = 2**16
IPV6 = 6


class CacheFillMethod(Enum):
    """The approach we want to use when updating our redis cache."""

    LAZY: Annotated[int, "Wait until the cache is expired to update it"] = 1
    EAGER: Annotated[int, "Request all prefixes from GoBGP and put them into the cache"] = 2
    EXPIRE: Annotated[int, "Force expire the given redis cache."] = 3


logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)


class GoBGP:
    """Represents a GoBGP instance."""

    def __init__(self, url):
        """Configure the channel used for communication."""
        channel = grpc.insecure_channel(url)
        self.stub = gobgp_pb2_grpc.GobgpApiStub(channel)
        self.redis_connection = redis.StrictRedis.from_url(
            "redis://redis", port=6379, db=1, decode_responses=True
        )  # TODO figure out db number and grab this from settings

    @staticmethod
    def _get_family_afi(ip_version):
        if ip_version == IPV6:
            return gobgp_pb2.Family.AFI_IP6
        return gobgp_pb2.Family.AFI_IP

    def _build_path(self, ip, event_data=None):  # noqa: PLR0914
        # Grab ASN and Community from our event_data, or use the defaults
        if not event_data:
            event_data = {}
        asn = event_data.get("asn", DEFAULT_ASN)
        community = event_data.get("community", DEFAULT_COMMUNITY)
        ip_version = ip.ip.version

        # Set the origin to incomplete (options are IGP, EGP, incomplete)
        # Incomplete means that BGP is unsure of exactly how the prefix was injected into the topology.
        # The most common scenario here is that the prefix was redistributed into Border Gateway Protocol
        # from some other protocol, typically an IGP. - https://www.kwtrain.com/blog/bgp-pt2
        origin = Any()
        origin.Pack(
            attribute_pb2.OriginAttribute(
                origin=2,
            ),
        )

        # IP prefix and its associated length
        nlri = Any()
        nlri.Pack(
            attribute_pb2.IPAddressPrefix(
                prefix_len=ip.network.prefixlen,
                prefix=str(ip.ip),
            ),
        )

        # Set the next hop to the correct value depending on IP family
        next_hop = Any()
        family_afi = self._get_family_afi(ip_version)
        if ip_version == IPV6:
            next_hops = event_data.get("next_hop", DEFAULT_V6_NEXTHOP)
            next_hop.Pack(
                attribute_pb2.MpReachNLRIAttribute(
                    family=gobgp_pb2.Family(afi=family_afi, safi=gobgp_pb2.Family.SAFI_UNICAST),
                    next_hops=[next_hops],
                    nlris=[nlri],
                ),
            )
        else:
            next_hops = event_data.get("next_hop", DEFAULT_V4_NEXTHOP)
            next_hop.Pack(
                attribute_pb2.NextHopAttribute(
                    next_hop=next_hops,
                ),
            )

        # Set our AS Path
        as_path = Any()
        as_segment = None

        # Make sure our asn is an acceptable value.
        asn_is_valid(asn)
        as_segment = [attribute_pb2.AsSegment(numbers=[asn])]
        as_segments = attribute_pb2.AsPathAttribute(segments=as_segment)
        as_path.Pack(as_segments)

        # Set our community number
        # The ASN gets packed into the community so we need to be careful about size to not overflow the structure
        communities = Any()
        # Standard community
        # Since we pack both into the community string we need to make sure they will both fit
        if asn < MAX_SMALL_ASN and community < MAX_SMALL_COMM:
            # We bitshift ASN left by 16 so that there is room to add the community on the end of it. This is because
            # GoBGP wants the community sent as a single integer.
            comm_id = (asn << 16) + community
            communities.Pack(attribute_pb2.CommunitiesAttribute(communities=[comm_id]))
        else:
            logger.info("LargeCommunity Used - ASN: %s. Community: %s", asn, community)
            global_admin = asn
            local_data1 = community
            # set to 0 because there's no use case for it, but we need a local_data2 for gobgp to read any of it
            local_data2 = 0
            large_community = attribute_pb2.LargeCommunity(
                global_admin=global_admin,
                local_data1=local_data1,
                local_data2=local_data2,
            )
            communities.Pack(attribute_pb2.LargeCommunitiesAttribute(communities=[large_community]))

        attributes = [origin, next_hop, as_path, communities]

        return gobgp_pb2.Path(
            nlri=nlri,
            pattrs=attributes,
            family=gobgp_pb2.Family(afi=family_afi, safi=gobgp_pb2.Family.SAFI_UNICAST),
        )

    def add_path(self, ip, vrf, event_data):
        """Announce a single route."""
        logger.info("Blocking %s in VRF %s", ip, vrf)  # TODO: Do we want to name the None Case?

        try:
            path = self._build_path(ip, event_data)

            if vrf != "base":
                self.stub.AddPath(
                    gobgp_pb2.AddPathRequest(table_type=gobgp_pb2.VRF, path=path, vrf_id=vrf),
                    _TIMEOUT_SECONDS,
                )
            else:
                self.stub.AddPath(
                    gobgp_pb2.AddPathRequest(table_type=gobgp_pb2.GLOBAL, path=path),
                    _TIMEOUT_SECONDS,
                )
        except ASNError as e:
            logger.warning("ASN assertion failed with error: %s", e)

        self.update_prefix_cache(vrf, CacheFillMethod.EAGER)

    def del_all_paths(self, vrf):
        """Remove all routes from being announced from a given VRF."""
        logger.warning("Withdrawing ALL routes for VRF %s", vrf)

        if vrf == "base":
            self.stub.DeletePath(gobgp_pb2.DeletePathRequest(table_type=gobgp_pb2.GLOBAL), _TIMEOUT_SECONDS)
        if vrf != "base":
            self.stub.DeletePath(
                gobgp_pb2.DeletePathRequest(table_type=gobgp_pb2.VRF, vrf_id=vrf), _TIMEOUT_SECONDS
            )  # TODO: Test

        # Invalidate the cache entirely
        self.update_prefix_cache(vrf, CacheFillMethod.EXPIRE)  # TODO: Fix VRF

        logger.warning("Done withdrawing ALL routes for VRF %s", vrf)

    def del_path(self, ip, vrf, event_data):
        """Remove a single route from being announced."""
        logger.info("Unblocking %s in VRF %s", ip, vrf)  # TODO: Do we want to name the None Case?

        try:
            path = self._build_path(ip, event_data)

            if vrf != "base":
                self.stub.DeletePath(
                    gobgp_pb2.DeletePathRequest(table_type=gobgp_pb2.VRF, path=path, vrf_id=vrf),
                    _TIMEOUT_SECONDS,
                )
            else:
                self.stub.DeletePath(
                    gobgp_pb2.DeletePathRequest(table_type=gobgp_pb2.GLOBAL, path=path),
                    _TIMEOUT_SECONDS,
                )
        except ASNError as e:
            logger.warning("ASN assertion failed with error: %s", e)

        self.update_prefix_cache(vrf, CacheFillMethod.EAGER)

    def get_cache_ttl(self, cache_key: str) -> int:
        """get_cache_ttl gets the current TTL value for the provided cache key.

        Args:
            cache_key (str): The redis key you want to check TTL on.

        Returns:
            ttl(int): The remaining TTL that the cache is valid for. -2 means the key doesn't exist, and -1
                means that the key exists but has no associated expiration time.
        """
        logger.info("Checking cache TTL for cache %s", cache_key)
        ttl = self.redis_connection.ttl(cache_key)
        logger.info("Found cache TTL for cache %s. Cache is valid for %s more seconds", cache_key, ttl)
        return ttl

    def update_prefix_cache(self, vrf, cache_fill_method: CacheFillMethod = CacheFillMethod.LAZY) -> int:
        """update_prefix_cache ensures that the redis prefix cache is up to date.

        This method takes a VRF and an optional directive to how we should fill the prefix cache. The prefix
        cache is formatted as a redis key per VRF that we store the currently blocked routes in. This is cached
        for the default cache time so that we don't have to query GoBGP for the full route table for every single
        route that we need to see the block status for. This is necessary, unfortunately, because GoBGP doesn't
        let you see if a single route is in its route table for VRFs, so we have to grab the full table, which is
        potentially expensive in large deployments, and hold on to it for the TTL.

        In SCRAM, this data is used to display to a user if the route is blocked in the `/entries/` page.

        Args:
            vrf (str, optional): The VRF we're updating. Defaults to "base".
            cache_fill_method (CacheFillMethod, optional): The cache fill approach we want to use. Defaults to
                CacheFillMethod.LAZY which only updates the cache if the TTL is expired. CacheFillMethod.EAGER
                can be used to require that the entire cache is updated, and CacheFillMethod.EXPIRE will empty
                the cache completely.

        Returns:
            ttl(int): The remaining TTL that the cache is valid for. -2 means the key doesn't exist, and -1
                means that the key exists but has no associated expiration time.
        """
        # TODO: Write tests to cover this
        redis_key = f"route-table-{vrf}"

        match cache_fill_method:
            case CacheFillMethod.LAZY:
                logger.info("Lazily updating prefix check cache %s", redis_key)
                # Don't bother filling the cache if it was filled within the last 60 seconds. Is this a bad idea?
                if (ttl := self.get_cache_ttl(redis_key)) > 0:
                    logger.info("Prefix check on cache %s has %ss left, not updating cache", redis_key, ttl)
                    return ttl
            case CacheFillMethod.EXPIRE:
                self.redis_connection.expire(redis_key, 0)
            case CacheFillMethod.EAGER:
                logger.info("Updating the cache %s ✨with feeling✨", redis_key)

        # Now that we're in the scenario where we need to walk the whole route table, let's open a transaction and do
        # the redis portions of this all at once.
        with self.redis_connection.pipeline(transaction=True) as redis_transaction:
            logger.debug("Entering Redis Transaction")
            # We delete the entire cache since we're already refilling it from scratch. This gets rid of stale entries.
            redis_transaction.delete(redis_key)
            # Regardless of a lazy or eager approach, if the cache is already expired, we need to fill it:
            for prefix in self.get_all_prefixes(vrf):
                if vrf != "base":
                    ip = str(strip_distinguished_prefix(prefix.destination.prefix))
                else:
                    ip = str(prefix.destination.prefix)
                logger.info("Adding prefix %s to cache %s", ip, redis_key)
                redis_transaction.sadd(redis_key, ip)
            # Next, let's set this key to expire so that we don't hold onto these indefinitely.
            redis_transaction.expire(redis_key, PREFIX_CACHE_TIMEOUT_SECONDS)
            transaction_result = redis_transaction.execute()
            logger.debug("Redis transaction completed with result: %s", transaction_result)

        ttl = self.get_cache_ttl(redis_key)
        logger.info("Finished updating prefix cache %s, TTL is currently %ss", redis_key, ttl)

        return ttl

    def get_all_prefixes(self, vrf):
        """get_all_prefixes TODO.

        _extended_summary_

        Args:
            vrf (str, optional): _description_. Defaults to "base".

        Returns:
            _type_: _description_
        """
        # TODO: Write tests to cover this
        # VRFs require special consideration when talking to GoBGP.
        if vrf != "base":
            logger.info("Getting all prefixes from GoBGP for VRF %s", vrf)
            result_v4 = self.stub.ListPath(
                gobgp_pb2.ListPathRequest(
                    table_type=gobgp_pb2.VRF,
                    name=vrf,
                    family=gobgp_pb2.Family(afi=self._get_family_afi(4), safi=gobgp_pb2.Family.SAFI_UNICAST),
                ),
                _TIMEOUT_SECONDS,
            )
            result_v6 = self.stub.ListPath(
                gobgp_pb2.ListPathRequest(
                    table_type=gobgp_pb2.VRF,
                    name=vrf,
                    family=gobgp_pb2.Family(afi=self._get_family_afi(6), safi=gobgp_pb2.Family.SAFI_UNICAST),
                ),
                _TIMEOUT_SECONDS,
            )

            results = list(result_v4) + list(result_v6)
            logger.info("Found %s prefixes in vrf %s", len(results), vrf)

            return results

        # The non-VRF route table (base) needs to be handled this way with GoBGP.
        logger.info("Getting all prefixes from GoBGP for base routing instance")
        result_v4_vrf = self.stub.ListPath(
            gobgp_pb2.ListPathRequest(
                table_type=gobgp_pb2.GLOBAL,
                family=gobgp_pb2.Family(afi=self._get_family_afi(4), safi=gobgp_pb2.Family.SAFI_UNICAST),
            ),
            _TIMEOUT_SECONDS,
        )
        result_v6_vrf = self.stub.ListPath(
            gobgp_pb2.ListPathRequest(
                table_type=gobgp_pb2.GLOBAL,
                family=gobgp_pb2.Family(afi=self._get_family_afi(6), safi=gobgp_pb2.Family.SAFI_UNICAST),
            ),
            _TIMEOUT_SECONDS,
        )

        results = list(result_v4_vrf) + list(result_v6_vrf)
        logger.info("Found %s prefixes in base routing instance", len(results))

        return results

    def is_blocked(self, ip: IPv6Interface | IPv4Interface, vrf: str) -> bool:
        """Return True if at least one route matching the prefix is being announced."""
        logger.info("Checking to see if IP %s in VRF %s is blocked", ip, vrf)

        # TODO: Write tests to cover this
        # First let's make sure our redis cache is filled for this VRF:
        self.update_prefix_cache(vrf, CacheFillMethod.LAZY)

        # Next, simply ask Redis if it is in the cache. This is nice and fast!
        if self.redis_connection.sismember(f"route-table-{vrf}", str(ip)):
            logger.info("Found exact match prefix blocking IP %s in VRF %s", ip, vrf)
            return True

        # Then, In the more complicated case of the given IP only being blocked by a covering prefix
        # NOTE: Today, we don't ever query for these things in the frontend, but we might in the future.
        redis_cache_values = self.redis_connection.smembers(f"route-table-{vrf}")
        if any(ip in ip_network(prefix) for prefix in redis_cache_values):
            logger.info("Found covering prefix blocking IP %s in VRF %s", ip, vrf)
            return True

        # Finally, report back that we didn't find a block covering this IP.
        logger.info("Did not find any prefixes blocking IP %s in VRF %s", ip, vrf)
        logger.debug(redis_cache_values)
        return False
