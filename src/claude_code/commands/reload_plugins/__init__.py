"""Migrated from: commands/reload-plugins/index.ts"""

from __future__ import annotations

from claude_code.commands.spec import CommandSpec

RELOAD_PLUGINS_COMMAND = CommandSpec(
    type="local",
    name="reload-plugins",
    description="Activate pending plugin changes in the current session",
    supports_non_interactive=False,
    load_symbol="claude_code.commands.reload_plugins.reload_plugins_impl",
)

__all__ = ["RELOAD_PLUGINS_COMMAND"]
