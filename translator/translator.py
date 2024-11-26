#!/usr/bin/env python3

"""Define the main event loop for the translator."""

import asyncio
import ipaddress
import json
import logging
import os

import websockets
from gobgp import GoBGP

from scram.utils import debug

logger = logging.getLogger(__name__)
debug.setup(base_port=56732)

KNOWN_MESSAGES = {
    "translator_add",
    "translator_remove",
    "translator_remove_all",
    "translator_check",
}

# Must match the URL in asgi.py, and needs a trailing slash
hostname = os.environ.get("SCRAM_HOSTNAME", "scram_hostname_not_set")
url = os.environ.get("SCRAM_EVENTS_URL", "ws://django:8000/ws/route_manager/translator_block/")


async def process(message, websocket, g):
    """Take a single message form the websocket and hand it off to the appropriate function."""
    json_message = json.loads(message)
    event_type = json_message.get("type")
    event_data = json_message.get("message")
    if event_type not in KNOWN_MESSAGES:
        logger.error("Unknown event type received: %s", event_type)
    # TODO: Maybe only allow this in testing?
    elif event_type == "translator_remove_all":
        g.del_all_paths()
    else:
        try:
            ip = ipaddress.ip_interface(event_data["route"])
        except:  # noqa E722
            logger.exception("Error parsing message: %s", message)
            return

        if event_type == "translator_add":
            g.add_path(ip, event_data)
        elif event_type == "translator_remove":
            g.del_path(ip, event_data)
        elif event_type == "translator_check":
            json_message["type"] = "translator_check_resp"
            json_message["message"]["is_blocked"] = g.is_blocked(ip)
            json_message["message"]["translator_name"] = hostname
            await websocket.send(json.dumps(json_message))


async def main():
    """Connect to the websocket and start listening for messages."""
    g = GoBGP("gobgp:50051")
    async for websocket in websockets.connect(url):
        try:
            async for message in websocket:
                await process(message, websocket, g)

        except websockets.ConnectionClosed:
            continue


if __name__ == "__main__":
    logger.info("translator started")
    loop = asyncio.get_event_loop()
    loop.run_until_complete(main())
    loop.close()
