#!/usr/bin/env python3

import asyncio
import ipaddress
import json
import logging
import os

import websockets
from gobgp import GoBGP

# Here we setup a debugger if this is desired. This obviously should not be run in production.
debug_mode = os.environ.get("DEBUG")
if debug_mode:

    def install_deps():
        # Because of how we build translator currently, we don't have a great way to selectively install things at
        # build, so we just do it here! Right now this also includes base.txt, which is unecessary, but in the
        # future when we build a little better, it'll already be setup.
        logging.info("Installing dependencies for debuggers")

        import subprocess
        import sys

        subprocess.check_call([sys.executable, "-m", "pip", "install", "-r", "/requirements/local.txt"])

        logging.info("Done installing dependencies for debuggers")

    logging.info(f"Translator is set to use a debugger. Provided debug mode: {debug_mode}")
    # We have to setup the debugger appropriately for various IDEs. It'd be nice if they all used the same thing but
    # sadly, we live in a fallen world.
    if debug_mode == "pycharm-pydevd":
        logging.info("Entering debug mode for pycharm, make sure the debug server is running in PyCharm!")

        install_deps()

        import pydevd_pycharm

        pydevd_pycharm.settrace("host.docker.internal", port=56782, stdoutToServer=True, stderrToServer=True)

        logging.info("Debugger started.")
    elif debug_mode == "debugpy":
        logging.info("Entering debug mode for debugpy (VSCode)")

        install_deps()

        import debugpy

        debugpy.listen(("0.0.0.0", 56781))

        logging.info("Debugger listening on port 56781.")
    else:
        logging.warning(f"Invalid debug mode given: {debug_mode}. Debugger not started")

# Must match the URL in asgi.py, and needs a trailing slash
hostname = os.environ.get("SCRAM_HOSTNAME", "scram_hostname_not_set")
url = os.environ.get("SCRAM_EVENTS_URL", "ws://django:5000/ws/route_manager/translator_block/")


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
