"""
LSP Configuration.

Load and manage LSP server configurations from plugins.
"""

from __future__ import annotations

from ...utils.debug import log_for_debugging
from .types import ScopedLspServerConfig


async def get_all_lsp_servers() -> dict[str, ScopedLspServerConfig]:
    """Get all configured LSP servers from plugins.

    LSP servers are only supported via plugins, not user/project settings.

    Returns:
        Dict of server configurations keyed by scoped server name
    """
    all_servers: dict[str, ScopedLspServerConfig] = {}

    try:
        # In a full implementation, this would:
        # 1. Load all enabled plugins
        # 2. Extract LSP server configs from each plugin
        # 3. Scope server names by plugin name

        log_for_debugging(
            "info",
            f"Total LSP servers loaded: {len(all_servers)}",
        )

    except Exception as error:
        log_for_debugging(
            "error",
            f"Error loading LSP servers: {error}",
        )

    return all_servers
