"""
Semver-based “new version available” toast gating.

Migrated from: hooks/useUpdateNotification.ts
"""

from __future__ import annotations

from packaging.version import InvalidVersion, Version


def get_semver_part(version: str) -> str:
    try:
        v = Version(version)
        return f"{v.major}.{v.minor}.{v.micro}"
    except InvalidVersion:
        return version


def should_show_update_notification(updated_version: str, last_notified_semver: str | None) -> bool:
    return get_semver_part(updated_version) != (last_notified_semver or "")


def next_update_notification_state(
    updated_version: str | None,
    last_notified_semver: str | None,
    initial_semver: str,
) -> tuple[str | None, str | None]:
    """
    Returns ``(display_semver_or_none, new_last_notified)`` for UI + state write.

    Mirrors useUpdateNotification render-phase state update.
    """
    base = last_notified_semver if last_notified_semver is not None else get_semver_part(initial_semver)
    if not updated_version:
        return None, base
    us = get_semver_part(updated_version)
    if us != base:
        return us, us
    return None, base
