"""Env-less bridge core (ported from bridge/remoteBridgeCore.ts — skeleton)."""

from __future__ import annotations

import logging
from collections.abc import Callable
from typing import Any, TypedDict

from claude_code.bridge.code_session_api import RemoteCredentials, fetch_remote_credentials

logger = logging.getLogger(__name__)


class EnvLessBridgeParams(TypedDict, total=False):
    base_url: str
    get_access_token: Callable[[], str | None]
    on_inbound_message: Callable[[dict[str, Any]], Any]
    on_permission_response: Callable[[dict[str, Any]], None]
    on_state_change: Callable[[str, str | None], None]
    perpetual: bool
    outbound_only: bool
    tags: list[str]
    trusted_device_token: str | None


async def init_env_less_bridge_core(params: EnvLessBridgeParams) -> Any | None:
    """TODO: port ~1000 lines — poll, transport, flush gate, token scheduler."""
    logger.debug("[bridge:repl] init_env_less_bridge_core stub")
    _ = params
    return None


async def fetch_remote_credentials_export(
    session_id: str,
    base_url: str,
    access_token: str,
    timeout_ms: float,
    trusted_device_token: str | None = None,
) -> RemoteCredentials | None:
    """Re-export for SDK consumers matching TS remoteBridgeCore export."""
    return await fetch_remote_credentials(session_id, base_url, access_token, timeout_ms, trusted_device_token)
