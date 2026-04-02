"""
Process-lifetime host adapter for computer-use MCP.

Migrated from: utils/computerUse/hostAdapter.ts
"""

from __future__ import annotations

from types import SimpleNamespace
from typing import Any

from ..debug import log_for_debugging
from .common import COMPUTER_USE_MCP_SERVER_NAME
from .executor import CliExecutorOptions, create_cli_executor
from .gates import get_chicago_sub_gates, is_computer_use_enabled
from .swift_loader import require_computer_use_swift
from .types import Logger


class DebugLogger(Logger):
    def silly(self, message: str, *args: object) -> None:
        log_for_debugging(message % args if args else message, level="debug")

    def debug(self, message: str, *args: object) -> None:
        log_for_debugging(message % args if args else message, level="debug")

    def info(self, message: str, *args: object) -> None:
        log_for_debugging(message % args if args else message, level="info")

    def warn(self, message: str, *args: object) -> None:
        log_for_debugging(message % args if args else message, level="warn")

    def error(self, message: str, *args: object) -> None:
        log_for_debugging(message % args if args else message, level="error")


_cached_adapter: Any | None = None


def get_computer_use_host_adapter() -> Any:
    global _cached_adapter
    if _cached_adapter is not None:
        return _cached_adapter

    sub = get_chicago_sub_gates()

    async def ensure_os_permissions() -> dict[str, Any]:
        cu = require_computer_use_swift()
        accessibility = cu.tcc.checkAccessibility()
        screen_recording = cu.tcc.checkScreenRecording()
        if accessibility and screen_recording:
            return {"granted": True}
        return {
            "granted": False,
            "accessibility": accessibility,
            "screenRecording": screen_recording,
        }

    _cached_adapter = SimpleNamespace(
        serverName=COMPUTER_USE_MCP_SERVER_NAME,
        logger=DebugLogger(),
        executor=create_cli_executor(
            CliExecutorOptions(
                get_mouse_animation_enabled=lambda: sub.mouseAnimation,
                get_hide_before_action_enabled=lambda: sub.hideBeforeAction,
            ),
        ),
        ensureOsPermissions=ensure_os_permissions,
        isDisabled=lambda: not is_computer_use_enabled(),
        getSubGates=get_chicago_sub_gates,
        getAutoUnhideEnabled=lambda: True,
        cropRawPatch=lambda *a, **k: None,
    )
    return _cached_adapter
