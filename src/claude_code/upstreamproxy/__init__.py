"""
CCR upstream proxy module.

Handles proxy configuration for Claude Code Remote sessions.

Migrated from: upstreamproxy/*.ts
"""

from .proxy import (
    SESSION_TOKEN_PATH,
    UpstreamProxyState,
    get_proxy_state,
    init_upstream_proxy,
    is_proxy_enabled,
)
from .relay import (
    start_upstream_proxy_relay,
    stop_upstream_proxy_relay,
)

__all__ = [
    # Proxy
    "SESSION_TOKEN_PATH",
    "UpstreamProxyState",
    "init_upstream_proxy",
    "get_proxy_state",
    "is_proxy_enabled",
    # Relay
    "start_upstream_proxy_relay",
    "stop_upstream_proxy_relay",
]
