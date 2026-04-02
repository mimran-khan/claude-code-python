"""
Tracks tool uses auto-approved by bash / transcript classifiers.

Migrated from: utils/classifierApprovals.ts
"""

from __future__ import annotations

import os
from collections.abc import Callable
from dataclasses import dataclass
from typing import Literal

ClassifierName = Literal["bash", "auto-mode"]


@dataclass
class ClassifierApproval:
    classifier: ClassifierName
    matched_rule: str | None = None
    reason: str | None = None


_classifier_approvals: dict[str, ClassifierApproval] = {}
_classifier_checking: set[str] = set()
_classifier_listeners: set[Callable[[], None]] = set()


def _bash_classifier_enabled() -> bool:
    return os.environ.get("CLAUDE_CODE_BASH_CLASSIFIER", "").lower() in (
        "1",
        "true",
        "yes",
    )


def _transcript_classifier_enabled() -> bool:
    return os.environ.get("CLAUDE_CODE_TRANSCRIPT_CLASSIFIER", "").lower() in (
        "1",
        "true",
        "yes",
    )


def subscribe_classifier_checking(listener: Callable[[], None]) -> Callable[[], None]:
    _classifier_listeners.add(listener)

    def unsubscribe() -> None:
        _classifier_listeners.discard(listener)

    return unsubscribe


def _emit_checking() -> None:
    for fn in list(_classifier_listeners):
        fn()


def set_classifier_approval(tool_use_id: str, matched_rule: str) -> None:
    if not _bash_classifier_enabled():
        return
    _classifier_approvals[tool_use_id] = ClassifierApproval(
        classifier="bash",
        matched_rule=matched_rule,
    )


def get_classifier_approval(tool_use_id: str) -> str | None:
    if not _bash_classifier_enabled():
        return None
    approval = _classifier_approvals.get(tool_use_id)
    if approval is None or approval.classifier != "bash":
        return None
    return approval.matched_rule


def set_yolo_classifier_approval(tool_use_id: str, reason: str) -> None:
    if not _transcript_classifier_enabled():
        return
    _classifier_approvals[tool_use_id] = ClassifierApproval(
        classifier="auto-mode",
        reason=reason,
    )


def get_yolo_classifier_approval(tool_use_id: str) -> str | None:
    if not _transcript_classifier_enabled():
        return None
    approval = _classifier_approvals.get(tool_use_id)
    if approval is None or approval.classifier != "auto-mode":
        return None
    return approval.reason


def set_classifier_checking(tool_use_id: str) -> None:
    if not _bash_classifier_enabled() and not _transcript_classifier_enabled():
        return
    _classifier_checking.add(tool_use_id)
    _emit_checking()


def clear_classifier_checking(tool_use_id: str) -> None:
    if not _bash_classifier_enabled() and not _transcript_classifier_enabled():
        return
    _classifier_checking.discard(tool_use_id)
    _emit_checking()


def is_classifier_checking(tool_use_id: str) -> bool:
    return tool_use_id in _classifier_checking


def delete_classifier_approval(tool_use_id: str) -> None:
    _classifier_approvals.pop(tool_use_id, None)


def clear_classifier_approvals() -> None:
    _classifier_approvals.clear()
    _classifier_checking.clear()
    _emit_checking()
