#!/usr/bin/env python3

"""Define the main event loop for the translator."""

import asyncio
import ipaddress
import json
import logging
import os
from ipaddress import IPv4Interface, IPv6Interface
from typing import NamedTuple

import websockets
from exceptions import MessageError
from gobgp import GoBGP
from websockets.legacy.client import WebSocketClientProtocol

logger = logging.getLogger(__name__)

GOBGP_URL = "gobgp:50051"

REDIS_URL = "redis://redis"
REDIS_PORT = 6379
REDIS_DB_INDEX = 1

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
        which is unnecessary, but in the future when we build a little better, it'll already be
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


# TODO: Consider moving to pydantic to make message parsing easier.
class ParsedMessage(NamedTuple):
    """A parsed WebSocket message.

    Attributes:
        json_message (dict): The JSON representation of the original message.
        event_type (str): The type of event (e.g., "translator_add").
        event_data (dict): The event_data websocket message originally sent.
        vrf (str): The VRF value the message applies to.
        ip (IPv4Interface | IPv6Interface | None): The parsed IP address, or None if invalid or missing.
    """

    json_message: dict
    event_type: str
    event_data: dict
    vrf: str
    ip: IPv4Interface | IPv6Interface | None


def parse_message(message: str) -> ParsedMessage:
    """parse_message takes a websocket message, validates the parts, and splits it into variables that we can use.

    Args:
        message (str): The websocket message to parse

    Raises:
        MessageError: If we run across something we can't parse, we raise MessageError.

    Returns:
        ParsedMessage: The NamedTuple containing all the cleaned up data.
    """
    # Convert the message to JSON so we can work with it.
    json_message = json.loads(message)
    logger.info("Processing message %s", json_message)

    # Figure out the event type and make sure it's valid.
    event_type = json_message.get("type")
    logger.debug("Parsed message and found event_type: %s", event_type)

    # Separate out the event_data for future use.
    event_data = json_message.get("message")

    # Parse the VRF value and provide a default for backwards compatibility.
    try:
        vrf = json_message["message"]["vrf"]
        logger.debug("Parsed message and found VRF: %s", vrf)
    except KeyError:
        vrf = "base"
        logger.warning(
            "Websocket received without VRF Specified. Defaulting to base, however, this might change in the future. "
            "To avoid future issues, explicitly provide a VRF value in the websocket message like {'vrf':'test-vrf'}."
        )
        logger.debug("Parsed message and found no VRF, using `base`")

    # Parse the IP address value if it exists.
    try:
        ip = ipaddress.ip_interface(event_data.get("route"))
    except ValueError:
        ip = None
        logger.warning("Invalid IP: %s provided in message: %s", event_data.get("route"), message)

    # Now that we've got all the parts, lets do some basic validation on the validity of the message:
    if event_type not in KNOWN_MESSAGES:
        logger.error("Unknown event type received: %s", event_type)
        raise MessageError
    if event_type != "translator_remove_all" and not ip:
        logger.error(
            "IP address wasn't provided in message. "
            "This is required by all message types except `translator_remove_all`. Message was: %s",
            message,
        )
        raise MessageError

    # Finally, pack it all into our named tuple and return!
    return ParsedMessage(json_message, event_type, event_data, vrf, ip)


async def process(message: str, websocket: WebSocketClientProtocol, g: GoBGP) -> None:
    """Process takes a single message from the websocket and hands it off to the appropriate function.

    Args:
        message (str): The websocket message that we need to process.
        websocket (WebSocketClientProtocol): The websocket client for sending messages back to SCRAM Django.
        g (GoBGP): A GoBGP Client instance for actually *doing* stuff on the network.
    """
    try:
        json_message, event_type, event_data, vrf, ip = parse_message(message)
    except MessageError:
        logger.exception("Skipping message because we could not parse it: %s", message)
        return
    except Exception:
        # We want to catch all possible exceptions as we don't want one bad message to crash the entire translator.
        logger.exception("Something really horrible happened, skipping this message and logging the exception.")

    match event_type:
        case "translator_remove_all":
            # TODO: Maybe only allow this in testing?
            logger.info("Processing `translator_remove_all` message")
            g.del_all_paths(vrf)
            logger.info("Done processing `translator_remove_all` message")
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
    g = GoBGP(GOBGP_URL, REDIS_URL, REDIS_PORT, REDIS_DB_INDEX)
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
