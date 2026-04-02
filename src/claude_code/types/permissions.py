"""
Permission types.

Pure permission type definitions extracted to break import cycles.

Migrated from: types/permissions.ts (442 lines)
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Literal

# ============================================================================
# Permission Modes
# ============================================================================

EXTERNAL_PERMISSION_MODES = [
    "acceptEdits",
    "bypassPermissions",
    "default",
    "dontAsk",
    "plan",
]

ExternalPermissionMode = Literal[
    "acceptEdits",
    "bypassPermissions",
    "default",
    "dontAsk",
    "plan",
]

InternalPermissionMode = Literal[
    "acceptEdits",
    "bypassPermissions",
    "default",
    "dontAsk",
    "plan",
    "auto",
    "bubble",
]

PermissionMode = InternalPermissionMode

INTERNAL_PERMISSION_MODES = [
    "acceptEdits",
    "bypassPermissions",
    "default",
    "dontAsk",
    "plan",
    "auto",  # Only available with TRANSCRIPT_CLASSIFIER feature
]

PERMISSION_MODES = INTERNAL_PERMISSION_MODES


# ============================================================================
# Permission Behaviors
# ============================================================================

PermissionBehavior = Literal["allow", "deny", "ask"]


# ============================================================================
# Permission Rules
# ============================================================================

PermissionRuleSource = Literal[
    "userSettings",
    "projectSettings",
    "localSettings",
    "flagSettings",
    "policySettings",
    "cliArg",
    "command",
    "session",
]


@dataclass
class PermissionRuleValue:
    """The value of a permission rule."""

    tool_name: str
    rule_content: str | None = None


@dataclass
class PermissionRule:
    """A permission rule with its source and behavior."""

    source: PermissionRuleSource
    rule_behavior: PermissionBehavior
    rule_value: PermissionRuleValue


# ============================================================================
# Permission Updates
# ============================================================================

PermissionUpdateDestination = Literal[
    "userSettings",
    "projectSettings",
    "localSettings",
    "session",
    "cliArg",
]

WorkingDirectorySource = PermissionRuleSource


@dataclass
class AdditionalWorkingDirectory:
    """An additional directory included in permission scope."""

    path: str
    source: WorkingDirectorySource


@dataclass
class AddRulesUpdate:
    """Update to add permission rules."""

    destination: PermissionUpdateDestination
    rules: list[PermissionRuleValue] = field(default_factory=list)
    behavior: PermissionBehavior = "allow"
    type: str = "addRules"


@dataclass
class ReplaceRulesUpdate:
    """Update to replace permission rules."""

    destination: PermissionUpdateDestination
    rules: list[PermissionRuleValue] = field(default_factory=list)
    behavior: PermissionBehavior = "allow"
    type: str = "replaceRules"


@dataclass
class RemoveRulesUpdate:
    """Update to remove permission rules."""

    destination: PermissionUpdateDestination
    rules: list[PermissionRuleValue] = field(default_factory=list)
    behavior: PermissionBehavior = "allow"
    type: str = "removeRules"


@dataclass
class SetModeUpdate:
    """Update to set permission mode."""

    destination: PermissionUpdateDestination
    mode: ExternalPermissionMode = "default"
    type: str = "setMode"


@dataclass
class AddDirectoriesUpdate:
    """Update to add directories."""

    destination: PermissionUpdateDestination
    directories: list[str] = field(default_factory=list)
    type: str = "addDirectories"


@dataclass
class RemoveDirectoriesUpdate:
    """Update to remove directories."""

    destination: PermissionUpdateDestination
    directories: list[str] = field(default_factory=list)
    type: str = "removeDirectories"


# Union type for all permission updates

PermissionUpdate = (
    AddRulesUpdate
    | ReplaceRulesUpdate
    | RemoveRulesUpdate
    | SetModeUpdate
    | AddDirectoriesUpdate
    | RemoveDirectoriesUpdate
)

# ============================================================================
# Permission Decisions & Results
# ============================================================================


@dataclass
class PermissionCommandMetadata:
    """Minimal command shape for permission metadata."""

    name: str
    description: str = ""


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


# Type alias for any permission decision
PermissionDecision = PermissionAllowDecision | PermissionAskDecision | PermissionDenyDecision


@dataclass
class PermissionResult:
    """Full permission result with decision and metadata."""

    decision: PermissionDecision
    tool_name: str = ""
    tool_input: dict[str, Any] = field(default_factory=dict)


# ============================================================================
# Permission Context
# ============================================================================


@dataclass
class ToolPermissionContext:
    """Context for tool permission checking."""

    cwd: str = ""
    project_root: str = ""
    always_allow_rules: dict[str, list[str]] = field(default_factory=dict)
    always_deny_rules: dict[str, list[str]] = field(default_factory=dict)
    ask_rules: dict[str, list[str]] = field(default_factory=dict)
    additional_directories: list[AdditionalWorkingDirectory] = field(default_factory=list)
    permission_mode: PermissionMode = "default"
    session_id: str = ""


def get_permission_behavior_priority(behavior: PermissionBehavior) -> int:
    """Get the priority of a permission behavior (higher = more restrictive)."""
    priorities = {
        "allow": 0,
        "ask": 1,
        "deny": 2,
    }
    return priorities.get(behavior, 0)


def merge_permission_behaviors(
    behaviors: list[PermissionBehavior],
) -> PermissionBehavior:
    """Merge multiple permission behaviors, returning the most restrictive."""
    if not behaviors:
        return "allow"

    return max(behaviors, key=get_permission_behavior_priority)
