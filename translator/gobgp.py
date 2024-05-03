import logging

import attribute_pb2
import gobgp_pb2
import gobgp_pb2_grpc
import grpc
from google.protobuf.any_pb2 import Any

_TIMEOUT_SECONDS = 1000
DEFAULT_ASN = 65400
DEFAULT_COMMUNITY = 666
DEFAULT_V4_NEXTHOP = "192.0.2.199"
DEFAULT_V6_NEXTHOP = "100::1"

logging.basicConfig(level=logging.DEBUG)


class GoBGP(object):
    def __init__(self, url):
        channel = grpc.insecure_channel(url)
        self.stub = gobgp_pb2_grpc.GobgpApiStub(channel)

    def _get_family_AFI(self, ip_version):
        if ip_version == 6:
            return gobgp_pb2.Family.AFI_IP6
        else:
            return gobgp_pb2.Family.AFI_IP

    def _build_path(self, ip, event_data={}):
        # Grab ASN and Community from our event_data, or use the defaults
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
            )
        )

        # IP prefix and its associated length
        nlri = Any()
        nlri.Pack(
            attribute_pb2.IPAddressPrefix(
                prefix_len=ip.network.prefixlen,
                prefix=str(ip.ip),
            )
        )

        # Set the next hop to the correct value depending on IP family
        next_hop = Any()
        family_afi = self._get_family_AFI(ip_version)
        if ip_version == 6:
            next_hops = event_data.get("next_hop", DEFAULT_V6_NEXTHOP)
            next_hop.Pack(
                attribute_pb2.MpReachNLRIAttribute(
                    family=gobgp_pb2.Family(afi=family_afi, safi=gobgp_pb2.Family.SAFI_UNICAST),
                    next_hops=[next_hops],
                    nlris=[nlri],
                )
            )
        else:
            next_hops = event_data.get("next_hop", DEFAULT_V4_NEXTHOP)
            next_hop.Pack(
                attribute_pb2.NextHopAttribute(
                    next_hop=next_hops,
                )
            )

        # Set our AS Path
        as_path = Any()
        as_segment = None

        # Make sure our asn is an acceptable number. This is the max as stated in rfc6996
        assert 0 < asn < 4294967295
        as_segment = [attribute_pb2.AsSegment(numbers=[asn])]
        as_segments = attribute_pb2.AsPathAttribute(segments=as_segment)
        as_path.Pack(as_segments)

        # Set our community number
        communities = Any()
        communities.Pack(attribute_pb2.CommunitiesAttribute(communities=[community]))

        attributes = [origin, next_hop, as_path, communities]

        return gobgp_pb2.Path(
            nlri=nlri,
            pattrs=attributes,
            family=gobgp_pb2.Family(afi=family_afi, safi=gobgp_pb2.Family.SAFI_UNICAST),
        )

    def add_path(self, ip, event_data):
        logging.info(f"Blocking {ip}")
        try:
            path = self._build_path(ip, event_data)

            self.stub.AddPath(
                gobgp_pb2.AddPathRequest(table_type=gobgp_pb2.GLOBAL, path=path),
                _TIMEOUT_SECONDS,
            )
        except AssertionError:
            logging.warning("ASN assertion failed")

    def del_all_paths(self):
        logging.warning("Withdrawing ALL routes")

        self.stub.DeletePath(gobgp_pb2.DeletePathRequest(table_type=gobgp_pb2.GLOBAL), _TIMEOUT_SECONDS)

    def del_path(self, ip, event_data):
        logging.info(f"Unblocking {ip}")
        try:
            path = self._build_path(ip, event_data)
            self.stub.DeletePath(
                gobgp_pb2.DeletePathRequest(table_type=gobgp_pb2.GLOBAL, path=path),
                _TIMEOUT_SECONDS,
            )
        except AssertionError:
            logging.warning("ASN assertion failed")

    def get_prefixes(self, ip):
        prefixes = [gobgp_pb2.TableLookupPrefix(prefix=str(ip.ip))]
        family_afi = self._get_family_AFI(ip.ip.version)
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
        return len(self.get_prefixes(ip)) > 0
