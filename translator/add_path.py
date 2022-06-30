#!/usr/bin/env python3

import asyncio
import ipaddress
import json
import logging
import os

import websockets
from gobgp import GoBGP

# Must match the URL in asgi.py, and needs a trailing slash
hostname = os.environ.get("SCRAM_HOSTNAME", "vlad_laptop")
url = os.environ.get("SCRAM_EVENTS_URL", "ws://django:8000/ws/route_manager/xlator_block/")


async def main():
    g = GoBGP("gobgp:50051")
    async for websocket in websockets.connect(url):
        try:
            async for message in websocket:
                json_message = json.loads(message)
                event_type = json_message.get('type')
                event_data = json_message.get('message')
                if event_type in ['add_block', 'remove_block', 'check_block']:
                    try:
                        ip = ipaddress.ip_interface(event_data['route'])
                    except:  # noqa E722
                        logging.error(f"Error parsing message: {message!r}")
                        continue
                    if event_type == "add_block":
                        g.add_path(ip)
                    elif event_type == 'remove_block':
                        g.del_path(ip)
                    elif event_type == 'check_block':
                        json_message['type'] = 'check_block_resp'
                        json_message['message']['is_blocked'] = g.is_blocked(ip)
                        json_message['message']['xlator_name'] = hostname
                        await websocket.send(json.dumps(json_message))
        except websockets.ConnectionClosed:
            continue


if __name__ == "__main__":
    logging.info("add_path started")
    loop = asyncio.get_event_loop()
    loop.run_until_complete(main())
    loop.close()
