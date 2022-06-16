#!/usr/bin/env python3

import ipaddress
import logging

import attribute_pb2
import gobgp_pb2
import gobgp_pb2_grpc
import grpc
import walrus
from google.protobuf.any_pb2 import Any

_TIMEOUT_SECONDS = 1000

logging.basicConfig(level=logging.DEBUG)

db = walrus.Database(host="redis")
cg = db.consumer_group("cg-west", ["block_add", "block_remove", "status_request"])
cg.create()
cg.set_id("$")


def get_family(ip_version):
    if ip_version == 6:
        return gobgp_pb2.Family.AFI_IP6
    else:
        return gobgp_pb2.Family.AFI_IP


def build_path(ip, cidr_size, ip_version):
    origin = Any()
    origin.Pack(
        attribute_pb2.OriginAttribute(
            origin=2,  # INCOMPLETE
        )
    )

    nlri = Any()
    nlri.Pack(
        attribute_pb2.IPAddressPrefix(
            prefix_len=cidr_size,
            prefix=ip,
        )
    )

    next_hop = Any()
    family = get_family(ip_version)

    if ip_version == 6:
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
                next_hop="192.0.2.1",
            )
        )

    communities = Any()
    comm_id = (293 << 16) + 666
    communities.Pack(attribute_pb2.CommunitiesAttribute(communities=[comm_id]))

    attributes = [origin, next_hop, communities]

    return gobgp_pb2.Path(
        nlri=nlri,
        pattrs=attributes,
        family=gobgp_pb2.Family(afi=family, safi=gobgp_pb2.Family.SAFI_UNICAST),
    )


def block(ip, cidr_size, ip_version, redis_id):
    logging.info(f"Blocking {ip}/{cidr_size}")

    # Connect to GoBGP (Docker) on gRPC
    channel = grpc.insecure_channel("gobgp:50051")
    stub = gobgp_pb2_grpc.GobgpApiStub(channel)

    stub.AddPath(
        gobgp_pb2.AddPathRequest(
            table_type=gobgp_pb2.GLOBAL,
            path=build_path(ip, cidr_size, ip_version),
        ),
        _TIMEOUT_SECONDS,
    )


def unblock(ip, cidr_size, ip_version, redis_id):
    logging.info(f"Unblocking {ip}/{cidr_size}")
    print(f"Unblocking {ip}/{cidr_size}")

    # Connect to GoBGP (Docker) on gRPC
    channel = grpc.insecure_channel("gobgp:50051")
    stub = gobgp_pb2_grpc.GobgpApiStub(channel)

    stub.DeletePath(
        gobgp_pb2.DeletePathRequest(
            table_type=gobgp_pb2.GLOBAL,
            path=build_path(ip, cidr_size, ip_version),
        ),
        _TIMEOUT_SECONDS,
    )


def get_status(ip, cidr_size, ip_version, redis_id):
    logging.warning("Received get_status call")
    # Connect to GoBGP (Docker) on gRPC
    channel = grpc.insecure_channel("gobgp:50051")
    stub = gobgp_pb2_grpc.GobgpApiStub(channel)

    prefixes = [gobgp_pb2.TableLookupPrefix(prefix=ip)]
    family = get_family(ip_version)
    response = stub.ListPath(gobgp_pb2.ListPathRequest(table_type=gobgp_pb2.GLOBAL, prefixes=prefixes, family=gobgp_pb2.Family(afi=family, safi=gobgp_pb2.Family.SAFI_UNICAST), ), _TIMEOUT_SECONDS)
    current_dests = [d for d in response]
    db.xadd("status_response", {"req_id": redis_id, "is_active": str(len(current_dests) > 0)})


def unknown(ip, cidr_size, ip_version):
    logging.warning(f"Unknown action for {ip}/{cidr_size}")


action_registry = {
    "block_add": block,
    "block_remove": unblock,
    "status_request": get_status,
}


def run():
    # TODO: block until we get a response
    unacked_msgs = cg.read()
    if not unacked_msgs:
        return

    logging.debug("Processing messages from redis")
    for stream_name, stream_msgs in unacked_msgs:
        stream_name = stream_name.decode("utf-8")
        action = action_registry.get(stream_name, unknown)
        for msg in stream_msgs:
            print(stream_name, msg)
            redis_id, data = msg
            ip, cidr_size = data[b"route"].decode("utf-8").split("/", 1)
            try:
                ip_address = ipaddress.ip_address(ip)
            except:  # noqa E722
                logging.error(f"Invalid IP address received: {ip}")
                continue
            action(ip, int(cidr_size), ip_address.version, redis_id)
            getattr(cg, str(stream_name)).ack(redis_id)


if __name__ == "__main__":
    logging.info("add_path started")
    while True:
        run()
