"""
Settings file change notifications.

Migrated from: utils/settings/changeDetector.ts — minimal port (signal + lifecycle).
"""

from __future__ import annotations

from collections.abc import Callable

from ..signal import VoidSignal

_settings_changed = VoidSignal()
_initialized = False


async def initialize() -> None:
    global _initialized
    if _initialized:
        return
    _initialized = True


async def dispose() -> None:
    global _initialized
    _initialized = False
    _settings_changed.clear()


def subscribe(listener: Callable[[], None]) -> Callable[[], None]:
    return _settings_changed.subscribe(listener)


def notify_settings_changed() -> None:
    _settings_changed.emit()


settings_change_detector = {
    "initialize": initialize,
    "dispose": dispose,
    "subscribe": subscribe,
}
