#!/usr/bin/env python3

"""Define the main event loop for the translator."""

import asyncio
import ipaddress
import json
import logging
import os

import websockets
from gobgp import GoBGP

logger = logging.getLogger(__name__)

KNOWN_MESSAGES = {
    "translator_add",
    "translator_remove",
    "translator_remove_all",
    "translator_check",
}

# Here we setup a debugger if this is desired. This obviously should not be run in production.
debug_mode = os.environ.get("DEBUG")
if debug_mode:

    def install_deps():
        """Install necessary dependencies for debuggers.

        Because of how we build translator currently, we don't have a great way to selectively
        install things at build, so we just do it here! Right now this also includes base.txt,
        which is unecessary, but in the future when we build a little better, it'll already be
        setup.
        """
        logger.info("Installing dependencies for debuggers")

        import subprocess  # noqa: S404, PLC0415
        import sys  # noqa: PLC0415

        subprocess.check_call([sys.executable, "-m", "pip", "install", "-r", "/requirements/local.txt"])  # noqa: S603 TODO: add this to the container build

        logger.info("Done installing dependencies for debuggers")

    logger.info("Translator is set to use a debugger. Provided debug mode: %s", debug_mode)
    # We have to setup the debugger appropriately for various IDEs. It'd be nice if they all used the same thing but
    # sadly, we live in a fallen world.
    if debug_mode == "pycharm-pydevd":
        logger.info("Entering debug mode for pycharm, make sure the debug server is running in PyCharm!")

        install_deps()

        import pydevd_pycharm

        pydevd_pycharm.settrace("host.docker.internal", port=56782, stdoutToServer=True, stderrToServer=True)

        logger.info("Debugger started.")
    elif debug_mode == "debugpy":
        logger.info("Entering debug mode for debugpy (VSCode)")

        install_deps()

        import debugpy

        debugpy.listen(("0.0.0.0", 56781))  # noqa S104 (doesn't like binding to all interfaces)

        logger.info("Debugger listening on port 56781.")
    else:
        logger.warning("Invalid debug mode given: %s. Debugger not started", debug_mode)

# Must match the URL in asgi.py, and needs a trailing slash
hostname = os.environ.get("SCRAM_HOSTNAME", "scram_hostname_not_set")
url = os.environ.get("SCRAM_EVENTS_URL", "ws://django:8000/ws/route_manager/translator_block/")


async def process(message, websocket, g):
    """Take a single message form the websocket and hand it off to the appropriate function."""
    json_message = json.loads(message)
    logger.info("Processing message %s", json_message)
    event_type = json_message.get("type")
    event_data = json_message.get("message")
    vrf = json_message["message"].get("vrf", "base")

    if event_type not in KNOWN_MESSAGES:
        logger.error("Unknown event type received: %s", event_type)
    # TODO: Maybe only allow this in testing?
    elif event_type == "translator_remove_all":
        # TODO: Needs to handle VRFs
        logger.info("Processing `translator_remove_all` message")
        g.del_all_paths(vrf)
        logger.info("Done processing `translator_remove_all` message")
    else:
        try:
            ip = ipaddress.ip_interface(event_data["route"])
        except:  # noqa E722
            logger.exception("Error parsing ip: %s in message: %s", event_data.get("route"), message)
            return

        match event_type:  # TODO VRFs for all of this potentially.
            case "translator_add":
                logger.info("Processing `translator_add` message")
                g.add_path(ip, vrf, event_data)
                logger.info("Done processing `translator_add` message")
            case "translator_remove":
                logger.info("Processing `translator_remove` message")
                g.del_path(ip, vrf, event_data)
                logger.info("Done processing `translator_remove` message")
            case "translator_check":
                logger.info("Processing `translator_check` message")
                json_message["type"] = "translator_check_resp"
                json_message["message"]["is_blocked"] = g.is_blocked(ip, vrf)
                json_message["message"]["last_seen"] = g.get_cache_ttl(f"route-table-{vrf}")
                json_message["message"]["translator_name"] = hostname
                logger.debug("Sending `translator_check_resp` message: %s", json_message)
                await websocket.send(json.dumps(json_message))
                logger.debug("Done sending `translator_check_resp` message: %s", json_message)
                logger.info("Done processing `translator_check` message")


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
