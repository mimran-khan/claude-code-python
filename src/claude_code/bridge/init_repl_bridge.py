"""REPL entry wiring for Remote Control (ported from bridge/initReplBridge.ts)."""

from __future__ import annotations

from collections.abc import Callable
from typing import Any, TypedDict

from claude_code.bridge.bridge_config import get_bridge_access_token, get_bridge_token_override
from claude_code.bridge.bridge_enabled import (
    is_bridge_enabled_blocking,
    is_cse_shim_enabled,
    is_env_less_bridge_enabled,
)
from claude_code.bridge.debug_utils import log_bridge_skip
from claude_code.bridge.env_less_bridge_config import check_env_less_bridge_min_version
from claude_code.bridge.repl_bridge import BridgeState, ReplBridgeHandle, init_bridge_core
from claude_code.bridge.session_id_compat import set_cse_shim_gate


class InitBridgeOptions(TypedDict, total=False):
    on_inbound_message: Callable[[dict[str, Any]], Any]
    on_permission_response: Callable[[dict[str, Any]], None]
    on_interrupt: Callable[[], None]
    on_set_model: Callable[[str | None], None]
    on_set_max_thinking_tokens: Callable[[int | None], None]
    on_set_permission_mode: Callable[[str], dict[str, Any]]
    on_state_change: Callable[[BridgeState, str | None], None]
    initial_messages: list[dict[str, Any]]
    get_messages: Callable[[], list[dict[str, Any]]]
    previously_flushed_uuids: set[str]
    initial_name: str | None
    perpetual: bool
    outbound_only: bool
    tags: list[str]


async def init_repl_bridge(options: InitBridgeOptions | None = None) -> ReplBridgeHandle | None:
    options = options or {}
    set_cse_shim_gate(is_cse_shim_enabled)

    if not await is_bridge_enabled_blocking():
        log_bridge_skip("not_enabled", "[bridge:repl] Skipping: bridge not enabled")
        return None

    if not get_bridge_access_token():
        log_bridge_skip("no_oauth", "[bridge:repl] Skipping: no OAuth tokens")
        cb = options.get("on_state_change")
        if cb:
            cb("failed", "/login")
        return None

    if not get_bridge_token_override():
        pass

    if is_env_less_bridge_enabled():
        verr = await check_env_less_bridge_min_version()
        if verr:
            cb = options.get("on_state_change")
            if cb:
                cb("failed", verr)
            return None
        return None

    core_params: dict[str, Any] = {
        "on_inbound_message": options.get("on_inbound_message"),
        "on_permission_response": options.get("on_permission_response"),
        "on_state_change": options.get("on_state_change"),
        "perpetual": options.get("perpetual", False),
        "outbound_only": options.get("outbound_only", False),
        "tags": options.get("tags"),
    }
    return await init_bridge_core(core_params)  # type: ignore[arg-type]
