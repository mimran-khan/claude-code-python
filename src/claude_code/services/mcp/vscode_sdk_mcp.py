"""
VS Code extension MCP bridge (notifications + experiment gates).

Migrated from: services/mcp/vscodeSdkMcp.ts

Full ``log_event`` notification handling requires the MCP SDK client handler API;
this module registers the client reference, sends ``experiment_gates``, and
supports ``file_updated`` notifications.
"""

from __future__ import annotations

import asyncio
import logging
import os
from typing import Any

from ...utils.debug import log_for_debugging
from ..analytics import (
    check_statsig_feature_gate_cached_may_be_stale,
    get_dynamic_config_cached_may_be_stale,
    get_feature_value_cached,
    log_event,
)

logger = logging.getLogger(__name__)

_vscode_mcp_client: Any | None = None


def _read_auto_mode_enabled_state() -> str | None:
    raw = get_dynamic_config_cached_may_be_stale("tengu_auto_mode_config", {})
    if not isinstance(raw, dict):
        return None
    v = raw.get("enabled")
    return v if v in ("enabled", "disabled", "opt-in") else None


def notify_vscode_file_updated(
    file_path: str,
    old_content: str | None,
    new_content: str | None,
) -> None:
    if os.environ.get("USER_TYPE") != "ant" or _vscode_mcp_client is None:
        return
    client = _vscode_mcp_client.client

    async def _send() -> None:
        try:
            await client.notification(
                method="file_updated",
                params={
                    "filePath": file_path,
                    "oldContent": old_content,
                    "newContent": new_content,
                },
            )
        except Exception as exc:
            log_for_debugging(f"[VSCode] Failed to send file_updated notification: {exc}")

    try:
        loop = asyncio.get_running_loop()
        loop.create_task(_send())
    except RuntimeError:
        asyncio.run(_send())


def setup_vscode_sdk_mcp(sdk_clients: list[Any]) -> None:
    """Attach to ``claude-vscode`` when present (internal ``ant`` builds)."""
    global _vscode_mcp_client
    _vscode_mcp_client = None
    for c in sdk_clients:
        if getattr(c, "name", None) == "claude-vscode" and getattr(c, "type", None) == "connected":
            _vscode_mcp_client = c
            break
    if _vscode_mcp_client is None:
        return

    client = _vscode_mcp_client.client
    try:
        if hasattr(client, "set_notification_handler"):
            from pydantic import BaseModel, ConfigDict, Field

            class LogEventParams(BaseModel):
                model_config = ConfigDict(populate_by_name=True, extra="allow")

                event_name: str = Field(alias="eventName")
                event_data: dict[str, Any] = Field(default_factory=dict, alias="eventData")

            class LogEventNotification(BaseModel):
                method: str = "log_event"
                params: LogEventParams

            def _handler(n: LogEventNotification) -> None:
                p = n.params
                safe: dict[str, bool | int | float | str | None] = {}
                for k, v in p.event_data.items():
                    if isinstance(v, (bool, int, float, str, type(None))):
                        safe[k] = v
                log_event(f"tengu_vscode_{p.event_name}", safe)

            client.set_notification_handler(LogEventNotification, _handler)
    except Exception as exc:
        logger.debug("vscode_log_event_handler_unavailable", extra={"reason": str(exc)})

    gates: dict[str, bool | str] = {
        "tengu_vscode_review_upsell": check_statsig_feature_gate_cached_may_be_stale("tengu_vscode_review_upsell"),
        "tengu_vscode_onboarding": check_statsig_feature_gate_cached_may_be_stale("tengu_vscode_onboarding"),
        "tengu_quiet_fern": bool(get_feature_value_cached("tengu_quiet_fern", False)),
        "tengu_vscode_cc_auth": bool(get_feature_value_cached("tengu_vscode_cc_auth", False)),
    }
    auto = _read_auto_mode_enabled_state()
    if auto is not None:
        gates["tengu_auto_mode_state"] = auto

    async def _gates() -> None:
        await client.notification(method="experiment_gates", params={"gates": gates})

    try:
        loop = asyncio.get_running_loop()
        loop.create_task(_gates())
    except RuntimeError:
        asyncio.run(_gates())
