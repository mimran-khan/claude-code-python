"""
Command specs registry (built-in specs + optional external loaders).

Migrated from: utils/bash/registry.ts
"""

from __future__ import annotations

from .command_spec import CommandSpec
from .specs import BUILTIN_COMMAND_SPECS

_spec_cache: dict[str, CommandSpec | None] = {}


async def load_fig_spec(command: str) -> CommandSpec | None:
    """Placeholder: TS loads @withfig/autocomplete; not bundled in Python port."""
    _ = command
    return None


async def get_command_spec(command: str) -> CommandSpec | None:
    if not command or "/" in command or "\\" in command:
        return None
    if ".." in command:
        return None
    if command.startswith("-") and command != "-":
        return None
    if command in _spec_cache:
        return _spec_cache[command]
    for spec in BUILTIN_COMMAND_SPECS:
        if spec.name == command:
            _spec_cache[command] = spec
            return spec
    fig = await load_fig_spec(command)
    _spec_cache[command] = fig
    return fig


__all__ = ["CommandSpec", "get_command_spec", "load_fig_spec"]
