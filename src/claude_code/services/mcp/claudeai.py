"""
Claude.ai org-configured MCP servers (HTTP API).

Migrated from: services/mcp/claudeai.ts
"""

from __future__ import annotations

import os
from typing import Any

import httpx

from ...constants.oauth import get_oauth_config
from ...mcp.types import McpClaudeAIProxyServerConfig, ScopedMcpServerConfig
from ...utils.debug import log_for_debugging
from ...utils.env_utils import is_env_defined_falsy
from ..analytics import log_event
from .normalization import normalize_name_for_mcp

FETCH_TIMEOUT_S = 5.0
MCP_SERVERS_BETA_HEADER = "mcp-servers-2025-12-04"

_claudeai_mcp_session_cache: dict[str, ScopedMcpServerConfig] | None = None


def clear_claude_ai_mcp_configs_cache() -> None:
    """Clear memoized fetch; call after login."""
    global _claudeai_mcp_session_cache
    _claudeai_mcp_session_cache = None
    from .client import clear_mcp_auth_cache

    clear_mcp_auth_cache()


def fetch_claude_ai_mcp_configs_if_eligible() -> dict[str, ScopedMcpServerConfig]:
    """
    Fetch MCP servers from Claude.ai when OAuth + ``user:mcp_servers`` scope.

    Result is cached for the process lifetime until ``clear_claude_ai_mcp_configs_cache``.
    """
    global _claudeai_mcp_session_cache
    if _claudeai_mcp_session_cache is not None:
        return dict(_claudeai_mcp_session_cache)

    if is_env_defined_falsy(os.environ.get("ENABLE_CLAUDEAI_MCP_SERVERS")):
        log_for_debugging("[claudeai-mcp] Disabled via env var")
        log_event("tengu_claudeai_mcp_eligibility", {"state": "disabled_env_var"})
        _claudeai_mcp_session_cache = {}
        return {}

    try:
        from ..oauth.client import get_claude_ai_oauth_tokens
    except ImportError:
        _claudeai_mcp_session_cache = {}
        return {}

    tokens = get_claude_ai_oauth_tokens()
    if not tokens or not tokens.access_token:
        log_for_debugging("[claudeai-mcp] No access token")
        log_event("tengu_claudeai_mcp_eligibility", {"state": "no_oauth_token"})
        _claudeai_mcp_session_cache = {}
        return {}

    if "user:mcp_servers" not in (tokens.scopes or []):
        log_for_debugging(
            f"[claudeai-mcp] Missing user:mcp_servers scope (scopes={','.join(tokens.scopes or []) or 'none'})"
        )
        log_event("tengu_claudeai_mcp_eligibility", {"state": "missing_scope"})
        _claudeai_mcp_session_cache = {}
        return {}

    base = get_oauth_config().BASE_API_URL.rstrip("/")
    url = f"{base}/v1/mcp_servers?limit=1000"
    log_for_debugging(f"[claudeai-mcp] Fetching from {url}")

    try:
        r = httpx.get(
            url,
            headers={
                "Authorization": f"Bearer {tokens.access_token}",
                "Content-Type": "application/json",
                "anthropic-beta": MCP_SERVERS_BETA_HEADER,
                "anthropic-version": "2023-06-01",
            },
            timeout=FETCH_TIMEOUT_S,
        )
        r.raise_for_status()
        body = r.json()
    except Exception:
        log_for_debugging("[claudeai-mcp] Fetch failed")
        _claudeai_mcp_session_cache = {}
        return {}

    data = body.get("data")
    if not isinstance(data, list):
        _claudeai_mcp_session_cache = {}
        return {}

    configs: dict[str, ScopedMcpServerConfig] = {}
    used_normalized: set[str] = set()

    for server in data:
        if not isinstance(server, dict):
            continue
        sid = server.get("id")
        surl = server.get("url")
        display = server.get("display_name")
        if not isinstance(sid, str) or not isinstance(surl, str) or not isinstance(display, str):
            continue
        base_name = f"claude.ai {display}"
        final_name = base_name
        final_norm = normalize_name_for_mcp(final_name)
        count = 1
        while final_norm in used_normalized:
            count += 1
            final_name = f"{base_name} ({count})"
            final_norm = normalize_name_for_mcp(final_name)
        used_normalized.add(final_norm)
        configs[final_name] = ScopedMcpServerConfig(
            config=McpClaudeAIProxyServerConfig(type="claudeai-proxy", url=surl, id=sid),
            scope="claudeai",
        )

    log_for_debugging(f"[claudeai-mcp] Fetched {len(configs)} servers")
    log_event("tengu_claudeai_mcp_eligibility", {"state": "eligible"})
    _claudeai_mcp_session_cache = dict(configs)
    return dict(configs)


def mark_claude_ai_mcp_connected(name: str) -> None:
    """Record successful connector connection (idempotent)."""
    try:
        from ...utils.config_utils import save_global_config
    except ImportError:
        return

    def _upd(current: dict[str, Any]) -> dict[str, Any]:
        seen = list(current.get("claudeAiMcpEverConnected") or [])
        if name in seen:
            return current
        return {**current, "claudeAiMcpEverConnected": [*seen, name]}

    save_global_config(_upd)


def has_claude_ai_mcp_ever_connected(name: str) -> bool:
    try:
        from ...utils.config_utils import load_global_config_dict
    except ImportError:
        return False
    return name in (load_global_config_dict().get("claudeAiMcpEverConnected") or [])
