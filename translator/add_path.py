#!/usr/bin/env python3

import asyncio
import ipaddress
import logging

from aiohttp_sse_client import client as sse_client
import attribute_pb2
import gobgp_pb2
import gobgp_pb2_grpc
import grpc
from google.protobuf.any_pb2 import Any

_TIMEOUT_SECONDS = 1000

logging.basicConfig(level=logging.DEBUG)

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


def block(ip, cidr_size, ip_version):
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


def unblock(ip, cidr_size, ip_version):
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


def get_status(ip, cidr_size, ip_version):
    logging.warning("Received get_status call")
    # Connect to GoBGP (Docker) on gRPC
    channel = grpc.insecure_channel("gobgp:50051")
    stub = gobgp_pb2_grpc.GobgpApiStub(channel)

    prefixes = [gobgp_pb2.TableLookupPrefix(prefix=ip)]
    family = get_family(ip_version)
    response = stub.ListPath(
        gobgp_pb2.ListPathRequest(
            table_type=gobgp_pb2.GLOBAL,
            prefixes=prefixes,
            family=gobgp_pb2.Family(afi=family, safi=gobgp_pb2.Family.SAFI_UNICAST),
        ),
        _TIMEOUT_SECONDS,
    )
    current_dests = [d for d in response]


def unknown(ip, cidr_size, ip_version):
    logging.warning(f"Unknown action for {ip}/{cidr_size}")


async def main():
    async with sse_client.EventSource('http://django/events') as event_source:
        async for event in event_source:
            if event.type in ['add', 'remove']:
                ip, cidr_size = data[b"route"].decode("utf-8").split("/", 1)
                try:
                    ip_address = ipaddress.ip_address(ip)
                except:  # noqa E722
                    logging.error(f"Invalid IP address received: {ip}")
                    continue
                if event.type == 'add':
                    block(ip, int(cidr_size), ip_address.version)
                else:
                    unblock(ip, int(cidr_size), ip_address.version)


if __name__ == "__main__":
    logging.info("add_path started")
    loop = asyncio.get_event_loop()
    loop.run_until_complete(main())
    loop.close()
