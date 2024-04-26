import logging

import attribute_pb2
import gobgp_pb2
import gobgp_pb2_grpc
import grpc
from google.protobuf.any_pb2 import Any

_TIMEOUT_SECONDS = 1000

logging.basicConfig(level=logging.DEBUG)


class GoBGP(object):
    def __init__(self, url):
        channel = grpc.insecure_channel(url)
        self.stub = gobgp_pb2_grpc.GobgpApiStub(channel)

    def _get_family(self, ip_version):
        if ip_version == 6:
            return gobgp_pb2.Family.AFI_IP6
        else:
            return gobgp_pb2.Family.AFI_IP

    def _build_path(self, ip, event_data):
        # defaults
        asn = 64500
        community = 666

        logging.debug(event_data)
        # Pull asn and community from event_data if we have any
        if event_data:
            if "asn" in event_data:
                asn = event_data["asn"]
            if "community" in event_data:
                community = event_data["community"]

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
        family = self._get_family(ip.ip.version)
        if family == 6:
            next_hop.Pack(
                attribute_pb2.MpReachNLRIAttribute(
                    family=gobgp_pb2.Family(afi=family, safi=gobgp_pb2.Family.SAFI_UNICAST),
                    next_hops=["100::1"],
                    nlris=[nlri],
                )
            )
        else:
            next_hop.Pack(
                attribute_pb2.NextHopAttribute(
                    next_hop="192.0.2.199",
                )
            )

        # Set our AS Path
        as_path = Any()
        as_segment = None

        # Make sure our asn is an acceptable number. This is the max as stated in rfc6996
        assert asn < 4294967295
        as_segment = [attribute_pb2.AsSegment(numbers=[asn])]
        as_segments = attribute_pb2.AsPathAttribute(segments=as_segment)
        as_path.Pack(as_segments)

        # Set our community number
        # TODO: We currently only accept one community number, we may want to accept more than one in the future
        communities = Any()
        communities.Pack(attribute_pb2.CommunitiesAttribute(communities=[community]))

        attributes = [origin, next_hop, as_path, communities]

        return gobgp_pb2.Path(
            nlri=nlri,
            pattrs=attributes,
            family=gobgp_pb2.Family(afi=family, safi=gobgp_pb2.Family.SAFI_UNICAST),
        )

    def add_path(self, ip, event_data):
        logging.info(f"Blocking {ip}")
        path = self._build_path(ip, event_data)

        self.stub.AddPath(
            gobgp_pb2.AddPathRequest(table_type=gobgp_pb2.GLOBAL, path=path),
            _TIMEOUT_SECONDS,
        )

    def del_all_paths(self):
        logging.warning("Withdrawing ALL routes")

        self.stub.DeletePath(gobgp_pb2.DeletePathRequest(table_type=gobgp_pb2.GLOBAL), _TIMEOUT_SECONDS)

    def del_path(self, ip, event_data):
        path = self._build_path(ip, event_data)

        logging.info(f"Unblocking {ip}")

        self.stub.DeletePath(
            gobgp_pb2.DeletePathRequest(table_type=gobgp_pb2.GLOBAL, path=path),
            _TIMEOUT_SECONDS,
        )

    def get_prefixes(self, ip):
        prefixes = [gobgp_pb2.TableLookupPrefix(prefix=str(ip.ip))]
        family = self._get_family(ip.ip.version)
        result = self.stub.ListPath(
            gobgp_pb2.ListPathRequest(
                table_type=gobgp_pb2.GLOBAL,
                prefixes=prefixes,
                family=gobgp_pb2.Family(afi=family, safi=gobgp_pb2.Family.SAFI_UNICAST),
            ),
            _TIMEOUT_SECONDS,
        )
        return list(result)

    def is_blocked(self, ip):
        return len(self.get_prefixes(ip)) > 0
