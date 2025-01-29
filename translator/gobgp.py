"""A translator interface for GoBGP (https://github.com/osrg/gobgp)."""

import logging

import attribute_pb2
import gobgp_pb2
import gobgp_pb2_grpc
import grpc
import redis
from exceptions import ASNError
from google.protobuf.any_pb2 import Any
from shared import asn_is_valid

_TIMEOUT_SECONDS = 1000
DEFAULT_ASN = 65400
DEFAULT_COMMUNITY = 666
DEFAULT_V4_NEXTHOP = "192.0.2.199"
DEFAULT_V6_NEXTHOP = "100::1"
MAX_SMALL_ASN = 2**16
MAX_SMALL_COMM = 2**16
IPV6 = 6

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

    def add_path(self, ip, event_data):
        """Announce a single route."""
        vrf_id = event_data.get("vrf_id")
        logger.info("Blocking %s in VRF %s", ip, vrf_id)  # TODO: Do we want to name the None Case?

        try:
            path = self._build_path(ip, event_data)

            if vrf_id:
                self.stub.AddPath(
                    gobgp_pb2.AddPathRequest(table_type=gobgp_pb2.VRF, path=path, vrf_id=vrf_id),
                    _TIMEOUT_SECONDS,
                )
            else:
                self.stub.AddPath(
                    gobgp_pb2.AddPathRequest(table_type=gobgp_pb2.GLOBAL, path=path),
                    _TIMEOUT_SECONDS,
                )
        except ASNError as e:
            logger.warning("ASN assertion failed with error: %s", e)

    def del_all_paths(self):
        """Remove all routes from being announced."""
        logger.warning("Withdrawing ALL routes")

        self.stub.DeletePath(gobgp_pb2.DeletePathRequest(table_type=gobgp_pb2.GLOBAL), _TIMEOUT_SECONDS)
        # TODO: Delete paths in all tables? Maybe GoBGP has a helper for this.

    def del_path(self, ip, event_data):
        """Remove a single route from being announced."""
        vrf_id = event_data.get("vrf_id")
        logger.info("Unblocking %s in VRF %s", ip, vrf_id)  # TODO: Do we want to name the None Case?

        try:
            path = self._build_path(ip, event_data)

            if vrf_id:
                self.stub.DeletePath(
                    gobgp_pb2.DeletePathRequest(table_type=gobgp_pb2.VRF, path=path, vrf_id=vrf_id),
                    _TIMEOUT_SECONDS,
                )
            else:
                self.stub.DeletePath(
                    gobgp_pb2.DeletePathRequest(table_type=gobgp_pb2.GLOBAL, path=path),
                    _TIMEOUT_SECONDS,
                )
        except ASNError as e:
            logger.warning("ASN assertion failed with error: %s", e)

    def update_prefix_cache(self, vrf="base"):
        """update_prefix_cache _summary_TODO.

        _extended_summary_

        Args:
            vrf (str, optional): _description_. Defaults to "base".

        Returns:
            _type_: _description_
        """
        logger.info("Updating prefix check cache")

        redis_key = f"route-table-{vrf}"
        expiration = 60

        # Don't bother filling the cache if it was filled within the last 60 seconds. Is this a bad idea?
        if (ttl := self.redis_connection.ttl(redis_key)) > 0:
            logger.info("Prefix check cache has %ss left, not updating cache", ttl)
            return ttl

        for prefix in self.get_all_prefixes():
            ip = str(prefix.destination.prefix)
            logger.info("Adding prefix %s to cache %s", ip, redis_key)
            self.redis_connection.sadd(redis_key, ip)

        # Finally, let's set this key to expire so that we don't hold onto these indefinitely.
        self.redis_connection.expire(redis_key, expiration)
        ttl = self.redis_connection.ttl(redis_key)
        logger.info("Finished updating prefix cache %s, set TTL to %s", redis_key, ttl)

        return ttl

    def get_all_prefixes(self, vrf="base"):
        """get_all_prefixes TODO.

        _extended_summary_

        Args:
            vrf (str, optional): _description_. Defaults to "base".

        Returns:
            _type_: _description_
        """
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

    def is_blocked(self, ip, vrf="base"):
        """Return True if at least one route matching the prefix is being announced."""
        return self.redis_connection.sismember(f"route-table-{vrf}", str(ip))
