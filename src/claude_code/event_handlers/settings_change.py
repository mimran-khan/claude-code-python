"""
Subscribe to settings file changes (disk / detector fan-out).

Migrated from: hooks/useSettingsChange.ts
"""

from __future__ import annotations

from collections.abc import Callable


def subscribe_settings_change(
    detector_subscribe: Callable[[Callable[[str], None]], Callable[[], None]],
    on_change: Callable[[str, object], None],
    load_settings: Callable[[], object],
) -> Callable[[], None]:
    """
    ``detector_subscribe`` is ``settings_change_detector.subscribe`` equivalent.

    Returns unsubscribe callable.
    """

    def handle(source: str) -> None:
        on_change(source, load_settings())

    return detector_subscribe(handle)
