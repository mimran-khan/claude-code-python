"""
Store subscription helper (non-React analogue of ``useIsClassifierChecking``).

Migrated from: utils/classifierApprovalsHook.ts
"""

from __future__ import annotations

from collections.abc import Callable

from .classifier_approvals import is_classifier_checking, subscribe_classifier_checking


def subscribe_is_classifier_checking(
    tool_use_id: str,
    callback: Callable[[bool], None],
) -> Callable[[], None]:
    """
    Invoke ``callback`` with the current checking flag whenever the store updates.

    Returns an unsubscribe function (same shape as ``subscribe_classifier_checking``).
    """

    def on_change() -> None:
        callback(is_classifier_checking(tool_use_id))

    unsub = subscribe_classifier_checking(on_change)
    on_change()
    return unsub


__all__ = ["subscribe_is_classifier_checking"]
