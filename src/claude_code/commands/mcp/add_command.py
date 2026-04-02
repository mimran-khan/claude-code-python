"""
Migrated from: commands/mcp/addCommand.ts — CLI `mcp add` registration.

Uses a Protocol for the Commander-like parent command so tests can pass a stub.
"""

from __future__ import annotations

from typing import Any, Protocol


class _CommandLike(Protocol):
    def command(self, *args: Any, **kwargs: Any) -> Any: ...


def register_mcp_add_command(mcp: _CommandLike) -> None:
    """Register the `mcp add` subcommand (parity with Commander setup in TS)."""

    _ = mcp.command(
        "add <name> <commandOrUrl> [args...]",
        description=(
            "Add an MCP server to Claude Code.\n\n"
            "Examples:\n"
            "  claude mcp add --transport http sentry https://mcp.sentry.dev/mcp\n"
            "  claude mcp add -e API_KEY=xxx my-server -- npx my-mcp-server\n"
        ),
    )
