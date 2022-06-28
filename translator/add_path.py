#!/usr/bin/env python3

import asyncio
import ipaddress
import json
import logging
import os

from aiohttp_sse_client import client as sse_client
from gobgp import GoBGP

# Must match the URL in asgi.py, and needs a trailing slash
url = os.environ.get("SCRAM_EVENTS_URL", "http://django:8000/events/blocks/")


async def main():
    g = GoBGP("gobgp:50051")
    async with sse_client.EventSource(url) as event_source:
        async for event in event_source:
            if event.type in ["add", "remove"]:
                data = json.loads(event.data)
                try:
                    ip = ipaddress.ip_interface(data["route"])
                except KeyError:  # noqa E722
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
