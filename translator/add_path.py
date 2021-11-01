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
cg = db.consumer_group("cg-west", ["block_add"])
cg.create()
cg.set_id("$")


def block(ip, cidr_size, ip_version):
    logging.info(f"Blocking {ip}/{cidr_size}")

    # Connect to GoBGP (Docker) on gRPC
    channel = grpc.insecure_channel("gobgp:50051")
    stub = gobgp_pb2_grpc.GobgpApiStub(channel)

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

    if ip_version == 6:
        family = gobgp_pb2.Family.AFI_IP6
        next_hop.Pack(
            attribute_pb2.MpReachNLRIAttribute(
                family=gobgp_pb2.Family(afi=family, safi=gobgp_pb2.Family.SAFI_UNICAST),
                next_hops=["::1"],
                nlris=[nlri],
            )
        )

    else:
        family = gobgp_pb2.Family.AFI_IP
        next_hop.Pack(
            attribute_pb2.NextHopAttribute(
                next_hop="10.87.3.66",
            )
        )

    communities = Any()
    comm_id = (294 << 16) + 666
    communities.Pack(attribute_pb2.CommunitiesAttribute(communities=[comm_id]))

    attributes = [origin, next_hop, communities]

    stub.AddPath(
        gobgp_pb2.AddPathRequest(
            table_type=gobgp_pb2.GLOBAL,
            path=gobgp_pb2.Path(
                nlri=nlri,
                pattrs=attributes,
                family=gobgp_pb2.Family(afi=family, safi=gobgp_pb2.Family.SAFI_UNICAST),
            ),
        ),
        _TIMEOUT_SECONDS,
    )


def run():
    # TODO: block
    unacked_msgs = cg.read()
    if not unacked_msgs:
        return

    logging.debug("Processing messages from redis")

    for stream_name, stream_msgs in unacked_msgs:
        for msg in stream_msgs:
            redis_id, data = msg
            ip, cidr_size = data[b"route"].decode("utf-8").split("/", 1)
            try:
                ip_address = ipaddress.ip_address(ip)
            except:  # noqa E722
                logging.error(f"Invalid IP address received: {ip}")
                continue
            block(ip, int(cidr_size), ip_address.version)
            cg.block_add.ack(redis_id)


if __name__ == "__main__":
    logging.info("add_path started")
    while True:
        run()
