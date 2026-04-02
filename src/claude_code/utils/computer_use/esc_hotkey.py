"""
Escape hotkey registration (stub; TS used CGEventTap via @ant/computer-use-swift).

Migrated from: utils/computerUse/escHotkey.ts
"""

from __future__ import annotations

from collections.abc import Callable

from ..debug import log_for_debugging
from .drain_run_loop import release_pump, retain_pump
from .swift_loader import require_computer_use_swift

_registered = False


def register_esc_hotkey(on_escape: Callable[[], None]) -> bool:
    global _registered
    if _registered:
        return True
    cu = require_computer_use_swift()
    if not cu.hotkey.registerEscape(on_escape):
        log_for_debugging("[cu-esc] registerEscape returned false", level="warn")
        return False
    retain_pump()
    _registered = True
    log_for_debugging("[cu-esc] registered")
    return True


def unregister_esc_hotkey() -> None:
    global _registered
    if not _registered:
        return
    try:
        require_computer_use_swift().hotkey.unregister()
    finally:
        release_pump()
        _registered = False
        log_for_debugging("[cu-esc] unregistered")


def notify_expected_escape() -> None:
    if not _registered:
        return
    require_computer_use_swift().hotkey.notifyExpectedEscape()
