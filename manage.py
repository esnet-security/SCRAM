#!/usr/bin/env python
"""Django's command-line utility for administrative tasks."""

import os
import sys
from pathlib import Path


def main():
    """Run administrative tasks."""
    os.environ.setdefault("DJANGO_SETTINGS_MODULE", "config.settings.local")
    try:
        from django.core.management import execute_from_command_line
    except ImportError as exc:
        msg = (
            "Couldn't import Django. Are you sure it's installed and "
            "available on your PYTHONPATH environment variable? Did you "
            "forget to activate a virtual environment?"
        )
        raise ImportError(
            msg,
        ) from exc

    # This allows easy placement of apps within the interior
    # scram directory.
    current_path = Path(__file__).parent.resolve()
    sys.path.append(str(current_path / "scram"))

    execute_from_command_line(sys.argv)


if __name__ == "__main__":
    main()
