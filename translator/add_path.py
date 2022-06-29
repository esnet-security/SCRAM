#!/usr/bin/env python3

import asyncio
import ipaddress
import json
import logging
import os

import websockets
from gobgp import GoBGP

# Must match the URL in asgi.py, and needs a trailing slash
url = os.environ.get("SCRAM_EVENTS_URL", "ws://django:8000/ws/route_manager/block/")


async def main():
    g = GoBGP("gobgp:50051")
    async for websocket in websockets.connect(url):
        try:
            async for message in websocket:
                json_message = json.loads(message)
                event_type = json_message.get('type')
                event_data = json_message.get('message')
                if event_type in ['add_block', 'remove_block']:
                    try:
                        ip = ipaddress.ip_interface(event_data['route'])
                    except:  # noqa E722
                        logging.error(f"Error parsing message: {message!r}")
                        continue
                    if event_type == "add_block":
                        g.add_path(ip)
                    else:
                        g.del_path(ip)
        except websockets.ConnectionClosed:
            continue


if __name__ == "__main__":
    logging.info("add_path started")
    loop = asyncio.get_event_loop()
    loop.run_until_complete(main())
    loop.close()
