#!/usr/bin/env python3

import asyncio
import ipaddress
import logging

from aiohttp_sse_client import client as sse_client
from gobgp import GoBGP


async def main():
    g = GoBGP("gobgp:50051")
    async with sse_client.EventSource("http://django/events") as event_source:
        async for event in event_source:
            if event.type in ["add", "remove"]:
                ip, cidr_size = event.data[b"route"].decode("utf-8").split("/", 1)
                try:
                    ip = ipaddress.ip_interface(ip, cidr_size)
                except:  # noqa E722
                    logging.error(f"Invalid IP address received: {ip}")
                    continue
                if event.type == "add":
                    g.add_path(ip)
                else:
                    g.del_path(ip)


if __name__ == "__main__":
    logging.info("add_path started")
    loop = asyncio.get_event_loop()
    loop.run_until_complete(main())
    loop.close()
