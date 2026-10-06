#!/usr/bin/env python3

"""Define the main event loop for the translator."""

import asyncio
import ipaddress
import json
import logging

from api import attribute_pb2, common_pb2, gobgp_pb2, gobgp_pb2_grpc, nlri_pb2
import websockets
from grpc import RpcError

from .gobgp import IPV4, IPV6, GoBGP
from .settings import DebuggerTypes, settings

logging.basicConfig(level=settings.log_level)
logger = logging.getLogger(__name__)

# These are really only messages we *receive*, we sometimes *send* others (translator_heartbeat)
KNOWN_MESSAGES = {
    "translator_block_add",
    "translator_block_remove",
    "translator_block_check",
    "translator_remove_all",
    "translator_add_flowspec",
    "translator_remove_flowspec",
    "translator_check_flowspec",
    "translator_all_flowspec", # TODO: Remove this testing piece when we have a better way of testing flowspec...
}

# Django closes with this code when no TranslatorType matches our SCRAM_EVENTS_URL; retrying can't fix it.
UNKNOWN_TRANSLATOR_TYPE = 4404

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
        
    # --- FLOWSPEC MESSAGE HANDLING ---
    elif event_type in ("translator_add_flowspec", "translator_remove_flowspec", "translator_check_flowspec", "translator_all_flowspec"):
        try:
            # Validate IPs if they are provided in the flowspec payload
            try:
                if event_data.get("destination"):
                    dest_ip = ipaddress.ip_interface(event_data.pop("destination"))
                if event_data.get("source"):
                    source_ip = ipaddress.ip_interface(event_data.pop("source"))
            except ValueError as e:
                logger.exception("Error parsing Flowspec IPs in message: %s", message)
                return
            
            # Pass the parsed event_data dictionary to the underlying GoBGP wrapper.
            # Expected fields inside event_data: destination, source, source-port, 
            # destination-port, protocol, action (e.g., "discard", "rate-limit")
            if event_type == "translator_add_flowspec":
                g.add_flowspec(source_ip, dest_ip, event_data)
            elif event_type == "translator_remove_flowspec":
                g.del_flowspec(source_ip, dest_ip, event_data)
            elif event_type == "translator_check_flowspec":
                g.check_flowspec(source_ip, dest_ip, event_data)
            elif event_type == "translator_all_flowspec": # TODO: Remove this testing piece when we have a better way of testing flowspec...
                print(g.check_flowspec(source_ip, dest_ip, event_data))
                g.add_flowspec(source_ip, dest_ip, event_data)
                print(g.check_flowspec(source_ip, dest_ip, event_data))
                g.del_flowspec(source_ip, dest_ip, event_data)
                print(g.check_flowspec(source_ip, dest_ip, event_data))

        except ValueError:
            logger.exception("Error parsing Flowspec IPs in message: %s", message)
            return
        except Exception:
            logger.exception("Error processing flowspec message: %s", message)
            return
            
    # --- STANDARD BGP ROUTE HANDLING ---
    else:
        try:
            ip = ipaddress.ip_interface(event_data["route"])
        except (ValueError, KeyError):
            logger.exception("Error parsing message: %s", message)
            return

        if event_type == "translator_block_add":
            g.add_path(ip, event_data)
        elif event_type == "translator_block_remove":
            g.del_path(ip, event_data)
        elif event_type == "translator_block_check":
            json_message["type"] = "translator_check_resp"
            json_message["message"]["is_blocked"] = g.is_blocked(ip)
            await websocket.send(json.dumps(json_message))


async def heartbeat(websocket, g):
    """Periodically send health status/route counts to Django."""
    while True:
        try:
            v4_count = g.get_route_count(IPV4)
            v6_count = g.get_route_count(IPV6)
            payload = {
                "type": "translator_heartbeat",
                "message": {
                    "v4_count": v4_count,
                    "v6_count": v6_count,
                },
            }
            logger.debug("Sending heartbeat: %s", json.dumps(payload))
            await websocket.send(json.dumps(payload))
        except Exception:
            logger.exception("Heartbeat failed")
        await asyncio.sleep(30)


def exit_if_rejected(closed):
    """Stop instead of reconnecting when SCRAM rejects our translator type."""
    if closed.rcvd and closed.rcvd.code == UNKNOWN_TRANSLATOR_TYPE:
        logger.critical("SCRAM rejected this translator: %s", closed.rcvd.reason)
        raise SystemExit(1) from closed


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
                except websockets.ConnectionClosed as e:
                    exit_if_rejected(e)
                    continue
                finally:
                    heartbeat_task.cancel()
        except RpcError as e:
            logger.warning("Encountered an error connecting to gobgp, retrying in 10s, error is: %s", e)
            await asyncio.sleep(10)
        except (OSError, websockets.InvalidURI) as e:
            logger.warning("Could not connect to SCRAM websocket, retrying in 10s, error is: %s", e)
            await asyncio.sleep(10)


if __name__ == "__main__":
    logger.info("translator started")
    loop = asyncio.get_event_loop()
    loop.run_until_complete(main())
    loop.close()