#!/usr/bin/env python3

import asyncio
import ipaddress
import json
import logging
import os

import websockets
from gobgp import GoBGP

# Must match the URL in asgi.py, and needs a trailing slash
hostname = os.environ.get("SCRAM_HOSTNAME", "scram_hostname_not_set")
url = os.environ.get("SCRAM_EVENTS_URL", "ws://django:8000/ws/route_manager/translator_block/")


async def main():
    g = GoBGP("gobgp:50051")
    async for websocket in websockets.connect(url):
        try:
            async for message in websocket:
                json_message = json.loads(message)
                event_type = json_message.get("type")
                event_data = json_message.get("message")
                if event_type not in [
                    "translator_add",
                    "translator_remove",
                    "translator_remove_all",
                    "translator_check",
                ]:
                    logging.error(f"Unknown event type received: {event_type!r}")
                # TODO: Maybe only allow this in testing?
                elif event_type == "translator_remove_all":
                    g.del_all_paths()
                else:
                    try:
                        ip = ipaddress.ip_interface(event_data["route"])
                    except:  # noqa E722
                        logging.error(f"Error parsing message: {message!r}")
                        continue

                    if event_type == "translator_add":
                        g.add_path(ip, event_data)
                    elif event_type == "translator_remove":
                        g.del_path(ip, event_data)
                    elif event_type == "translator_check":
                        json_message["type"] = "translator_check_resp"
                        json_message["message"]["is_blocked"] = g.is_blocked(ip)
                        json_message["message"]["translator_name"] = hostname
                        await websocket.send(json.dumps(json_message))

        except websockets.ConnectionClosed:
            continue


if __name__ == "__main__":
    logging.info("translator started")
    loop = asyncio.get_event_loop()
    loop.run_until_complete(main())
    loop.close()
