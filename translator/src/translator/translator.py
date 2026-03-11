#!/usr/bin/env python3

"""Define the main event loop for the translator."""

import asyncio
import ipaddress
import json
import logging

import gobgp_pb2
import websockets
from grpc import RpcError

from .gobgp import GoBGP
from .settings import DebuggerTypes, settings

logging.basicConfig(level=settings.log_level)
logger = logging.getLogger(__name__)

KNOWN_MESSAGES = {
    "translator_add",
    "translator_remove",
    "translator_remove_all",
    "translator_check",
}

# Here we setup a debugger if this is desired. This obviously should not be run in production.
if settings.debug:
    logger.info("Translator is set to use a debugger. Provided debug mode: %s", settings.debug)
    # We have to setup the debugger appropriately for various IDEs. It'd be nice if they all used the same thing but
    # sadly, we live in a fallen world.
    match settings.debug:
        case DebuggerTypes.PYCHARM_PYDEVD:
            logger.info("Entering debug mode for pycharm, make sure the debug server is running in PyCharm!")

            import pydevd_pycharm

            pydevd_pycharm.settrace("host.docker.internal", port=56782, stdoutToServer=True, stderrToServer=True)

            logger.info("Debugger started.")
        case DebuggerTypes.DEBUGPY:
            logger.info("Entering debug mode for debugpy (VSCode)")

            import debugpy

            debugpy.listen(("0.0.0.0", 56781))  # noqa S104 (doesn't like binding to all interfaces)

            logger.info("Debugger listening on port 56781.")


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
        except (ValueError, KeyError):
            logger.exception("Error parsing message: %s", message)
            return

        if event_type == "translator_add":
            g.add_path(ip, event_data)
        elif event_type == "translator_remove":
            g.del_path(ip, event_data)
        elif event_type == "translator_check":
            json_message["type"] = "translator_check_resp"
            json_message["message"]["is_blocked"] = g.is_blocked(ip)
            json_message["message"]["translator_name"] = settings.scram_hostname
            await websocket.send(json.dumps(json_message))


async def websocket_loop():
    """Connect to the websocket and start listening for messages for Gobgp."""
    logger.info("connecting to gobgp at %s", settings.gobgp_url)
    g = GoBGP(settings.gobgp_url)
    async for websocket in websockets.connect(settings.scram_events_url):
        try:
            async for message in websocket:
                await process(message, websocket, g)
        except websockets.ConnectionClosed:
            continue


async def heartbeat(websocket, g):
    """Periodically send health status/route counts to Django."""
    while True:
        try:
            v4_count = g.get_route_count(gobgp_pb2.Family.AFI_IP)
            v6_count = g.get_route_count(gobgp_pb2.Family.AFI_IP6)
            logger.info("Sending heartbeat: v4=%s, v6=%s", v4_count, v6_count)
            await websocket.send(
                json.dumps({
                    "message": {
                        "hostname": settings.translator_hostname,
                        "v4_count": v4_count,
                        "v6_count": v6_count,
                    },
                })
            )
        except Exception:
            logger.exception("Heartbeat failed")
        await asyncio.sleep(30)


async def main():
    """Connect to the websocket and start listening for messages."""
    while True:
        try:
            logger.info("connecting to gobgp at %s", settings.gobgp_url)
            g = GoBGP(settings.gobgp_url)
            async for websocket in websockets.connect(settings.scram_events_url):
                heartbeat_task = asyncio.create_task(heartbeat(websocket, g))
                try:
                    async for message in websocket:
                        await process(message, websocket, g)
                except websockets.ConnectionClosed:
                    heartbeat_task.cancel()
                    continue
                finally:
                    heartbeat_task.cancel()
        except RpcError:
            logger.exception("Heartbeat failed: could not reach GoBGP")
        await asyncio.sleep(10)


if __name__ == "__main__":
    logger.info("translator started")
    loop = asyncio.get_event_loop()
    loop.run_until_complete(main())
    loop.close()
