"""Converts environ-config's documentation to Markdown and writes it to the docs folder."""

import sys
from pathlib import Path

sys.path.append(".")

from config import cfg


def formatter(options):
    """Formats the help text to Markdown.

    Returns:
        str: A simple Markdown table with the env vars
    """
    result = "| Name | Description | Required | Default |\n"
    result += "|-|-|-|-|\n"
    for o in options:
        result += f"|{o['var_name']}|{o['help_str']}|{o['required']}|{o['default']!r}|\n"

    return result


def on_pre_build(config):
    """Handler from mkdocs hook."""
    with Path("docs/environment_variables.md").open("w", encoding="utf-8") as f:
        f.write(cfg.generate_help(formatter=formatter))
