"""
Hook types.

Type definitions for the hooks system.

Migrated from: types/hooks.ts (291 lines)
"""

from __future__ import annotations

from collections.abc import Callable
from dataclasses import dataclass, field
from typing import Any, Literal

# Hook event types
HookEvent = Literal[
    "PreToolUse",
    "PostToolUse",
    "PostToolUseFailure",
    "UserPromptSubmit",
    "SessionStart",
    "Setup",
    "SubagentStart",
    "PermissionDenied",
    "Notification",
    "PermissionRequest",
    "Elicitation",
    "ElicitationResult",
    "CwdChanged",
    "FileChanged",
    "WorktreeCreate",
]

HOOK_EVENTS: list[HookEvent] = [
    "PreToolUse",
    "PostToolUse",
    "PostToolUseFailure",
    "UserPromptSubmit",
    "SessionStart",
    "Setup",
    "SubagentStart",
    "PermissionDenied",
    "Notification",
    "PermissionRequest",
    "Elicitation",
    "ElicitationResult",
    "CwdChanged",
    "FileChanged",
    "WorktreeCreate",
]


def is_hook_event(value: str) -> bool:
    """Check if a string is a valid hook event."""
    return value in HOOK_EVENTS


@dataclass
class HookProgress:
    """Progress info for a running hook."""

    type: str = "hook_progress"
    hook_event: HookEvent = "SessionStart"
    hook_name: str = ""
    command: str = ""
    prompt_text: str | None = None
    status_message: str | None = None


@dataclass
class HookBlockingError:
    """A blocking error from a hook."""

    blocking_error: str = ""
    command: str = ""


@dataclass
class PermissionRequestResult:
    """Result of a permission request hook."""

    behavior: Literal["allow", "deny"] = "deny"
    updated_input: dict[str, Any] = field(default_factory=dict)
    message: str | None = None
    interrupt: bool = False


@dataclass
class HookResult:
    """Result of executing a hook."""

    outcome: Literal["success", "blocking", "non_blocking_error", "cancelled"] = "success"
    message: dict[str, Any] | None = None
    system_message: dict[str, Any] | None = None
    blocking_error: HookBlockingError | None = None
    prevent_continuation: bool = False
    stop_reason: str | None = None
    permission_behavior: Literal["ask", "deny", "allow", "passthrough"] | None = None
    hook_permission_decision_reason: str | None = None
    additional_context: str | None = None
    initial_user_message: str | None = None
    updated_input: dict[str, Any] | None = None
    updated_mcp_tool_output: Any = None
    permission_request_result: PermissionRequestResult | None = None
    retry: bool = False


@dataclass
class AggregatedHookResult:
    """Aggregated results from multiple hooks."""

    message: dict[str, Any] | None = None
    blocking_errors: list[HookBlockingError] = field(default_factory=list)
    prevent_continuation: bool = False
    stop_reason: str | None = None
    hook_permission_decision_reason: str | None = None
    permission_behavior: Literal["ask", "deny", "allow", "passthrough"] | None = None
    additional_contexts: list[str] = field(default_factory=list)
    initial_user_message: str | None = None
    updated_input: dict[str, Any] | None = None
    updated_mcp_tool_output: Any = None
    permission_request_result: PermissionRequestResult | None = None
    retry: bool = False


@dataclass
class HookCallbackContext:
    """Context passed to callback hooks for state access."""

    get_app_state: Callable[[], Any] | None = None
    update_attribution_state: Callable[[Callable], None] | None = None


@dataclass
class SyncHookOutput:
    """Output from a synchronous hook."""

    continue_execution: bool = True
    suppress_output: bool = False
    stop_reason: str | None = None
    decision: Literal["approve", "block"] | None = None
    reason: str | None = None
    system_message: str | None = None
    hook_specific_output: dict[str, Any] | None = None


@dataclass
class AsyncHookOutput:
    """Output from an asynchronous hook."""

    async_: bool = True
    async_timeout: float | None = None


def is_sync_hook_output(output: dict[str, Any]) -> bool:
    """Check if hook output is synchronous."""
    return not ("async" in output and output["async"] is True)


def is_async_hook_output(output: dict[str, Any]) -> bool:
    """Check if hook output is asynchronous."""
    return "async" in output and output["async"] is True


@dataclass
class HookInput:
    """Input payload for hook execution (tool lifecycle and related events)."""

    event: HookEvent = "PreToolUse"
    session_id: str = ""
    tool_name: str | None = None
    tool_input: dict[str, Any] | None = None
    tool_output: Any = None
    message: str | None = None
    cwd: str | None = None
    messages: list[Any] = field(default_factory=list)
    context: dict[str, Any] = field(default_factory=dict)
    data: dict[str, Any] = field(default_factory=dict)


# JSON-shaped hook output from external hooks; keep loose for wire interop.
HookOutput = dict[str, Any]
