"""A translator interface for GoBGP (https://github.com/osrg/gobgp)."""

import logging

import grpc
from google.protobuf.any_pb2 import Any

from . import attribute_pb2, gobgp_pb2, gobgp_pb2_grpc
from .exceptions import ASNError
from .shared import asn_is_valid

_TIMEOUT_SECONDS = 1000
DEFAULT_ASN = 65400
DEFAULT_COMMUNITY = 666
DEFAULT_V4_NEXTHOP = "192.0.2.199"
DEFAULT_V6_NEXTHOP = "100::1"
MAX_SMALL_ASN = 2**16
MAX_SMALL_COMM = 2**16
IPV6 = 6

logger = logging.getLogger(__name__)


class GoBGP:
    """Represents a GoBGP instance."""

    def __init__(self, url):
        """Configure the channel used for communication."""
        channel = grpc.insecure_channel(url)
        self.stub = gobgp_pb2_grpc.GobgpApiStub(channel)

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
        logger.info("Blocking %s", ip)
        try:
            path = self._build_path(ip, event_data)

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

    def del_path(self, ip, event_data):
        """Remove a single route from being announced."""
        logger.info("Unblocking %s", ip)
        try:
            path = self._build_path(ip, event_data)
            self.stub.DeletePath(
                gobgp_pb2.DeletePathRequest(table_type=gobgp_pb2.GLOBAL, path=path),
                _TIMEOUT_SECONDS,
            )
        except ASNError as e:
            logger.warning("ASN assertion failed with error: %s", e)

    def get_prefixes(self, ip):
        """Retrieve the routes that match a prefix and are announced.

        Returns:
            list: The routes that overlap with the prefix and are currently announced.
        """
        prefixes = [gobgp_pb2.TableLookupPrefix(prefix=str(ip.ip))]
        family_afi = self._get_family_afi(ip.ip.version)
        result = self.stub.ListPath(
            gobgp_pb2.ListPathRequest(
                table_type=gobgp_pb2.GLOBAL,
                prefixes=prefixes,
                family=gobgp_pb2.Family(afi=family_afi, safi=gobgp_pb2.Family.SAFI_UNICAST),
            ),
            _TIMEOUT_SECONDS,
        )
        return list(result)

    def is_blocked(self, ip):
        """Return True if at least one route matching the prefix is being announced."""
        return len(self.get_prefixes(ip)) > 0
