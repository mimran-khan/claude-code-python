"""
Common computer use constants and utilities.

Migrated from: utils/computerUse/common.ts
"""

from __future__ import annotations

import os

# MCP server name for computer use
COMPUTER_USE_MCP_SERVER_NAME = "computer-use"

# Sentinel bundle ID for CLI (no window)
CLI_HOST_BUNDLE_ID = "com.anthropic.claude-code.cli-no-window"

# Terminal bundle ID fallback map
TERMINAL_BUNDLE_ID_FALLBACK: dict[str, str] = {
    "iTerm.app": "com.googlecode.iterm2",
    "Apple_Terminal": "com.apple.Terminal",
    "ghostty": "com.mitchellh.ghostty",
    "kitty": "net.kovidgoyal.kitty",
    "WarpTerminal": "dev.warp.Warp-Stable",
    "vscode": "com.microsoft.VSCode",
}

# Static capabilities for macOS CLI
CLI_CU_CAPABILITIES = {
    "screenshotFiltering": "native",
    "platform": "darwin",
}


def get_cli_cu_capabilities() -> dict[str, str]:
    """Return static CLI computer-use capability flags (TS getCliCuCapabilities parity)."""
    return dict(CLI_CU_CAPABILITIES)


def get_terminal_bundle_id() -> str | None:
    """
    Get the bundle ID of the terminal emulator.

    Returns:
        Bundle ID or None if undetectable
    """
    # Check LaunchServices bundle identifier
    cf_bundle_id = os.getenv("__CFBundleIdentifier")
    if cf_bundle_id:
        return cf_bundle_id

    # Fallback to terminal type
    terminal = os.getenv("TERM_PROGRAM", "")
    return TERMINAL_BUNDLE_ID_FALLBACK.get(terminal)


def is_computer_use_mcp_server(name: str) -> bool:
    """
    Check if a server name is the computer use server.

    Args:
        name: Server name to check

    Returns:
        True if it's the computer use server
    """
    from ...services.mcp.normalization import normalize_name_for_mcp

    return normalize_name_for_mcp(name) == COMPUTER_USE_MCP_SERVER_NAME
