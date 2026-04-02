"""
Migrated from: commands/mcp/xaaIdpCommand.ts — CLI `mcp xaa` registration.
"""

from __future__ import annotations

from typing import Any, Protocol


class _CommandLike(Protocol):
    def command(self, *args: Any, **kwargs: Any) -> Any: ...


def register_mcp_xaa_idp_command(mcp: _CommandLike) -> None:
    """Register `mcp xaa` and nested setup subcommand (parity with TS)."""

    xaa_idp = mcp.command(
        "xaa",
        description="Manage the XAA (SEP-990) IdP connection",
    )
    _ = xaa_idp.command(
        "setup",
        description=("Configure the IdP connection (one-time setup for all XAA-enabled servers)"),
    )
