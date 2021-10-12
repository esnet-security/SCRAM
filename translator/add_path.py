#!/usr/bin/env python3

import grpc
from google.protobuf.any_pb2 import Any
import walrus

import gobgp_pb2
import gobgp_pb2_grpc
import attribute_pb2

_TIMEOUT_SECONDS = 1000

db = walrus.Database(host="redis")
cg = db.consumer_group('cg-west', ["block_add"])
cg.create()
cg.set_id('$')

def block(ip, cidr_size):
    channel = grpc.insecure_channel('gobgp:50051')
    stub = gobgp_pb2_grpc.GobgpApiStub(channel)

    nlri = Any()
    nlri.Pack(attribute_pb2.IPAddressPrefix(
        prefix_len=cidr_size,
        prefix=ip,
    ))
    origin = Any()
    origin.Pack(attribute_pb2.OriginAttribute(
        origin=2,  # INCOMPLETE
    ))
    as_segment = attribute_pb2.AsSegment(
        # type=2,  # "type" causes syntax error
        numbers=[100, 200],
    )
    as_segment.type = 2  # SEQ
    as_path = Any()
    as_path.Pack(attribute_pb2.AsPathAttribute(
        segments=[as_segment],
    ))
    next_hop = Any()
    next_hop.Pack(attribute_pb2.NextHopAttribute(
        next_hop="1.2.3.42",
    ))
    attributes = [origin, as_path, next_hop]

    stub.AddPath(
        gobgp_pb2.AddPathRequest(
            table_type=gobgp_pb2.GLOBAL,
            path=gobgp_pb2.Path(
                nlri=nlri,
                pattrs=attributes,
                family=gobgp_pb2.Family(afi=gobgp_pb2.Family.AFI_IP, safi=gobgp_pb2.Family.SAFI_UNICAST),
            )
        ),
        _TIMEOUT_SECONDS,
    )

def run():
    # TODO: block
    unacked_msgs = cg.read()
    if not unacked_msgs:
        return

    for stream_name, stream_msgs in unacked_msgs:
        for msg in stream_msgs:
            redis_id, data = msg
            ip, cidr_size = data[b'route'].decode('utf-8').split('/', 1)
            block(ip, int(cidr_size))
            cg.block_add.ack(redis_id)

if __name__ == '__main__':
    while True:
        run()
