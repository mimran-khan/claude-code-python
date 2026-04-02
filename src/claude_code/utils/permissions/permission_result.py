"""
Permission result types.

Defines the result types for permission checks.

Migrated from: utils/permissions/PermissionResult.ts (36 lines)
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Literal


@dataclass
class PermissionAllowDecision:
    """Result when permission is granted."""

    behavior: Literal["allow"] = "allow"
    updated_input: dict[str, Any] = field(default_factory=dict)
    user_modified: bool = False
    decision_reason: dict[str, Any] | None = None
    tool_use_id: str | None = None
    accept_feedback: str | None = None
    content_blocks: list[dict[str, Any]] = field(default_factory=list)


@dataclass
class PermissionAskDecision:
    """Result when user should be prompted."""

    behavior: Literal["ask"] = "ask"
    source_input: dict[str, Any] = field(default_factory=dict)
    tool_use_id: str | None = None
    decision_reason: dict[str, Any] | None = None
    pending_classifier_check: dict[str, Any] | None = None


@dataclass
class PermissionDenyDecision:
    """Result when permission is denied."""

    behavior: Literal["deny"] = "deny"
    reason: str = ""
    decision_reason: dict[str, Any] | None = None
    tool_use_id: str | None = None


# Union type for permission decisions
PermissionDecision = PermissionAllowDecision | PermissionAskDecision | PermissionDenyDecision


@dataclass
class PermissionResult:
    """Full permission result with decision and metadata."""

    behavior: Literal["allow", "deny", "ask"]
    decision: PermissionDecision | None = None
    tool_name: str = ""
    tool_input: dict[str, Any] = field(default_factory=dict)


def create_allow_decision(
    updated_input: dict[str, Any] | None = None,
    user_modified: bool = False,
    reason: dict[str, Any] | None = None,
) -> PermissionAllowDecision:
    """Create an allow decision."""
    return PermissionAllowDecision(
        updated_input=updated_input or {},
        user_modified=user_modified,
        decision_reason=reason,
    )


def create_deny_decision(
    reason: str,
    decision_reason: dict[str, Any] | None = None,
) -> PermissionDenyDecision:
    """Create a deny decision."""
    return PermissionDenyDecision(
        reason=reason,
        decision_reason=decision_reason,
    )


def create_ask_decision(
    source_input: dict[str, Any] | None = None,
    reason: dict[str, Any] | None = None,
) -> PermissionAskDecision:
    """Create an ask decision."""
    return PermissionAskDecision(
        source_input=source_input or {},
        decision_reason=reason,
    )


def is_allowed(decision: PermissionDecision) -> bool:
    """Check if a decision allows the action."""
    return decision.behavior == "allow"


def is_denied(decision: PermissionDecision) -> bool:
    """Check if a decision denies the action."""
    return decision.behavior == "deny"


def is_ask(decision: PermissionDecision) -> bool:
    """Check if a decision requires asking the user."""
    return decision.behavior == "ask"
