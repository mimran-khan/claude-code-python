"""
Config Tool.

Get or set Claude Code configuration settings.
"""

from .prompt import (
    CONFIG_TOOL_NAME,
    DESCRIPTION,
    generate_prompt,
)


def __getattr__(name: str):
    """Lazy import for ConfigTool."""
    if name == "ConfigTool":
        from .tool import ConfigTool

        return ConfigTool
    raise AttributeError(f"module {__name__!r} has no attribute {name!r}")


__all__ = [
    "CONFIG_TOOL_NAME",
    "DESCRIPTION",
    "generate_prompt",
    "ConfigTool",
]
