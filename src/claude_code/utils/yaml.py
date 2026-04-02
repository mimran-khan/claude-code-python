"""
YAML Utilities.

YAML parsing and serialization helpers.
"""

from __future__ import annotations

from typing import Any

import yaml


def parse_yaml(content: str) -> Any:
    """Parse YAML content.

    Args:
        content: The YAML string to parse

    Returns:
        The parsed YAML data
    """
    return yaml.safe_load(content)


def dump_yaml(data: Any, *, default_flow_style: bool = False) -> str:
    """Dump data to YAML string.

    Args:
        data: The data to serialize
        default_flow_style: If True, use flow style (inline) for collections

    Returns:
        The YAML string
    """
    return yaml.dump(
        data,
        default_flow_style=default_flow_style,
        allow_unicode=True,
        sort_keys=False,
    )


def safe_parse_yaml(content: str, default: Any = None) -> Any:
    """Parse YAML content safely, returning default on error.

    Args:
        content: The YAML string to parse
        default: The default value to return on error

    Returns:
        The parsed YAML data, or default on error
    """
    try:
        return yaml.safe_load(content)
    except Exception:
        return default
