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
        logging.debug(f"ip: {ip}, event_data: {event_data}")
        asn = event_data.get("asn", 64500)
        community = event_data.get("community", 666)

        origin = Any()
        origin.Pack(
            attribute_pb2.OriginAttribute(
                origin=2,  # INCOMPLETE
            )
        )

        nlri = Any()
        nlri.Pack(
            attribute_pb2.IPAddressPrefix(
                prefix_len=ip.network.prefixlen,
                prefix=str(ip.ip),
            )
        )

        next_hop = Any()
        family = self._get_family(ip.ip.version)

        if ip.ip.version == 6:
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

        communities = Any()
        comm_id = (asn << 16) + community
        communities.Pack(attribute_pb2.CommunitiesAttribute(communities=[comm_id]))

        attributes = [origin, next_hop, communities]

        return gobgp_pb2.Path(
            nlri=nlri,
            pattrs=attributes,
            family=gobgp_pb2.Family(afi=family, safi=gobgp_pb2.Family.SAFI_UNICAST),
        )

    def add_path(self, ip, event_data):
        logging.info(f"ip: {ip}, event_data: {event_data}")

        path = self._build_path(ip, event_data)

        logging.info(f"Blocking {event_data}")

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
