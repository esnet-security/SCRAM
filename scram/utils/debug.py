"""Enable either the PyCharm or debugpy debugger."""

import logging
import subprocess  # noqa: S404
import sys

from config import cfg

logger = logging.getLogger(__name__)


def setup(base_port=56780):
    """Setup a debugger if this is desired. This obviously should not be run in production.

    If using PyCharm, will start it on base_port + 1.
    If using debugpy, will start it on base_port.

    """
    if cfg.debugger:
        logger.info("Django is set to use a debugger. Provided debug mode: %s", cfg.debugger)
        if cfg.debugger == "pycharm-pydevd":
            logger.info("Entering debug mode for pycharm, make sure the debug server is running in PyCharm!")

            try:
                import pydevd_pycharm  # noqa: PLC0415
            except ImportError:
                logger.info("Installing pydevd_pycharm...")
                subprocess.check_call([sys.executable, "-m", "pip", "install", "pydevd-pycharm"])  # noqa: S603 TODO: add this to the container build
                import pydevd_pycharm  # noqa: PLC0415

                logger.info("Done installing pydevd_pycharm")

            pydevd_pycharm.settrace(
                "host.docker.internal", port=base_port + 1, stdoutToServer=True, stderrToServer=True
            )

            logger.info("pycharm-pydevd debugger started on host=host.docker.internal port=%d.", base_port + 1)
        elif cfg.debugger == "debugpy":
            logger.info("Entering debug mode for debugpy (VSCode)")

            try:
                import debugpy  # noqa: PLC0415
            except ImportError:
                logger.info("Installing debugpy...")
                subprocess.check_call([sys.executable, "-m", "pip", "install", "debugpy"])  # noqa: S603 TODO: add this to the container build
                import debugpy  # noqa: PLC0415

                logger.info("Done installing debugpy")

            debugpy.listen(("0.0.0.0", base_port))  # noqa S104 (doesn't like binding to all interfaces)

            logger.info("VScode debugpy debugger started on host=0.0.0.0 port=%d.", base_port)
