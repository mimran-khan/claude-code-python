"""REPL bridge core (ported from bridge/replBridge.ts — structure + TODO full loop)."""

from __future__ import annotations

import logging
from collections.abc import Callable
from typing import Any, Literal, TypedDict

# TODO: HybridTransport, bridge API, poll loop, token refresh, CCR v2 path

logger = logging.getLogger(__name__)

BridgeState = Literal["ready", "connected", "reconnecting", "failed"]


class ReplBridgeHandle(TypedDict, total=False):
    bridge_session_id: str
    disconnect: Callable[[], Any]
    subscribe_pr: Callable[..., Any]
    set_outbound_only: Callable[[bool], None]


class BridgeCoreParams(TypedDict, total=False):
    base_url: str
    get_access_token: Callable[[], str | None]
    on_inbound_message: Callable[[dict[str, Any]], Any]
    on_permission_response: Callable[[dict[str, Any]], None]
    on_state_change: Callable[[BridgeState, str | None], None]
    perpetual: bool
    outbound_only: bool
    environment_id: str | None
    tags: list[str] | None


async def init_bridge_core(params: BridgeCoreParams) -> ReplBridgeHandle | None:
    """Bootstrap-free bridge core (TODO: port ~2400 lines from replBridge.ts)."""
    logger.debug("[bridge:repl] init_bridge_core stub — TODO full implementation")
    _ = params
    return None


__all__ = [
    "BridgeCoreParams",
    "BridgeState",
    "ReplBridgeHandle",
    "init_bridge_core",
]
