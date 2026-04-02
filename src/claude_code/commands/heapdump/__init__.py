"""Migrated from: commands/heapdump/index.ts"""

from __future__ import annotations

from claude_code.commands.spec import CommandSpec

from .heapdump_impl import call, perform_heap_dump

HEAPDUMP_COMMAND = CommandSpec(
    type="local",
    name="heapdump",
    description="Dump the JS heap to ~/Desktop",
    hidden=True,
    supports_non_interactive=True,
    load_symbol="claude_code.commands.heapdump.heapdump_impl",
)

__all__ = ["HEAPDUMP_COMMAND", "call", "perform_heap_dump"]
