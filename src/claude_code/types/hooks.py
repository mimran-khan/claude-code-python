"""
Hook system type definitions.

Hooks allow external code to intercept and modify Claude Code behavior
at various points in the execution lifecycle.

Migrated from: types/hooks.ts (291 lines)
"""

from __future__ import annotations

from collections.abc import Awaitable, Callable
from dataclasses import dataclass, field
from typing import (
    TYPE_CHECKING,
    Any,
    Literal,
)

from pydantic import BaseModel

if TYPE_CHECKING:
    pass


# ============================================================================
# Hook Events
# ============================================================================

HOOK_EVENTS = (
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
)

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


def is_hook_event(value: str) -> bool:
    """Check if a string is a valid hook event."""
    return value in HOOK_EVENTS


# ============================================================================
# Prompt Elicitation Protocol Types
# ============================================================================


class PromptOption(BaseModel):
    """An option in a prompt request."""

    key: str
    label: str
    description: str | None = None


class PromptRequest(BaseModel):
    """
    A prompt request for user input.

    The `prompt` key acts as discriminator (mirroring the {async:true} pattern),
    with the id as its value.
    """

    prompt: str  # request id
    message: str
    options: list[PromptOption]


@dataclass
class PromptResponse:
    """Response to a prompt request."""

    prompt_response: str  # request id
    selected: str


# ============================================================================
# Hook Specific Output Types
# ============================================================================


@dataclass
class PreToolUseOutput:
    """Output specific to PreToolUse hooks."""

    hook_event_name: Literal["PreToolUse"] = "PreToolUse"
    permission_decision: Literal["allow", "deny", "ask"] | None = None
    permission_decision_reason: str | None = None
    updated_input: dict[str, Any] | None = None
    additional_context: str | None = None


@dataclass
class UserPromptSubmitOutput:
    """Output specific to UserPromptSubmit hooks."""

    hook_event_name: Literal["UserPromptSubmit"] = "UserPromptSubmit"
    additional_context: str | None = None


@dataclass
class SessionStartOutput:
    """Output specific to SessionStart hooks."""

    hook_event_name: Literal["SessionStart"] = "SessionStart"
    additional_context: str | None = None
    initial_user_message: str | None = None
    watch_paths: list[str] | None = None


@dataclass
class SetupOutput:
    """Output specific to Setup hooks."""

    hook_event_name: Literal["Setup"] = "Setup"
    additional_context: str | None = None


@dataclass
class SubagentStartOutput:
    """Output specific to SubagentStart hooks."""

    hook_event_name: Literal["SubagentStart"] = "SubagentStart"
    additional_context: str | None = None


@dataclass
class PostToolUseOutput:
    """Output specific to PostToolUse hooks."""

    hook_event_name: Literal["PostToolUse"] = "PostToolUse"
    additional_context: str | None = None
    updated_mcp_tool_output: Any | None = None


@dataclass
class PostToolUseFailureOutput:
    """Output specific to PostToolUseFailure hooks."""

    hook_event_name: Literal["PostToolUseFailure"] = "PostToolUseFailure"
    additional_context: str | None = None


@dataclass
class PermissionDeniedOutput:
    """Output specific to PermissionDenied hooks."""

    hook_event_name: Literal["PermissionDenied"] = "PermissionDenied"
    retry: bool = False


@dataclass
class NotificationOutput:
    """Output specific to Notification hooks."""

    hook_event_name: Literal["Notification"] = "Notification"
    additional_context: str | None = None


@dataclass
class PermissionRequestAllowDecision:
    """Allow decision for PermissionRequest hook."""

    behavior: Literal["allow"] = "allow"
    updated_input: dict[str, Any] | None = None
    updated_permissions: list[Any] | None = None  # list[PermissionUpdate]


@dataclass
class PermissionRequestDenyDecision:
    """Deny decision for PermissionRequest hook."""

    behavior: Literal["deny"] = "deny"
    message: str | None = None
    interrupt: bool = False


PermissionRequestDecision = PermissionRequestAllowDecision | PermissionRequestDenyDecision


@dataclass
class PermissionRequestOutput:
    """Output specific to PermissionRequest hooks."""

    hook_event_name: Literal["PermissionRequest"] = "PermissionRequest"
    decision: PermissionRequestDecision | None = None


@dataclass
class ElicitationOutput:
    """Output specific to Elicitation hooks."""

    hook_event_name: Literal["Elicitation"] = "Elicitation"
    action: Literal["accept", "decline", "cancel"] | None = None
    content: dict[str, Any] | None = None


@dataclass
class ElicitationResultOutput:
    """Output specific to ElicitationResult hooks."""

    hook_event_name: Literal["ElicitationResult"] = "ElicitationResult"
    action: Literal["accept", "decline", "cancel"] | None = None
    content: dict[str, Any] | None = None


@dataclass
class CwdChangedOutput:
    """Output specific to CwdChanged hooks."""

    hook_event_name: Literal["CwdChanged"] = "CwdChanged"
    watch_paths: list[str] | None = None


@dataclass
class FileChangedOutput:
    """Output specific to FileChanged hooks."""

    hook_event_name: Literal["FileChanged"] = "FileChanged"
    watch_paths: list[str] | None = None


@dataclass
class WorktreeCreateOutput:
    """Output specific to WorktreeCreate hooks."""

    hook_event_name: Literal["WorktreeCreate"] = "WorktreeCreate"
    worktree_path: str = ""


# Union of all hook-specific outputs
HookSpecificOutput = (
    PreToolUseOutput
    | UserPromptSubmitOutput
    | SessionStartOutput
    | SetupOutput
    | SubagentStartOutput
    | PostToolUseOutput
    | PostToolUseFailureOutput
    | PermissionDeniedOutput
    | NotificationOutput
    | PermissionRequestOutput
    | ElicitationOutput
    | ElicitationResultOutput
    | CwdChangedOutput
    | FileChangedOutput
    | WorktreeCreateOutput
)

# ============================================================================
# Hook Response Types
# ============================================================================


@dataclass
class SyncHookResponse:
    """Synchronous hook response."""

    continue_execution: bool = True
    suppress_output: bool = False
    stop_reason: str | None = None
    decision: Literal["approve", "block"] | None = None
    reason: str | None = None
    system_message: str | None = None
    hook_specific_output: HookSpecificOutput | None = None


@dataclass
class AsyncHookResponse:
    """Asynchronous hook response."""

    async_: bool = True
    async_timeout: int | None = None


# Union type for hook JSON output
HookJSONOutput = SyncHookResponse | AsyncHookResponse


def is_sync_hook_json_output(json: HookJSONOutput) -> bool:
    """Type guard to check if response is sync."""
    return not isinstance(json, AsyncHookResponse)


def is_async_hook_json_output(json: HookJSONOutput) -> bool:
    """Type guard to check if response is async."""
    return isinstance(json, AsyncHookResponse)


# ============================================================================
# Hook Input Type
# ============================================================================


@dataclass
class HookInput:
    """Input provided to hooks."""

    event: HookEvent = "PreToolUse"
    session_id: str = ""
    tool_name: str | None = None
    tool_input: dict[str, Any] | None = None
    tool_output: Any | None = None
    message: str | None = None
    cwd: str | None = None
    data: dict[str, Any] = field(default_factory=dict)


# ============================================================================
# Hook Callback Types
# ============================================================================


@dataclass
class HookCallbackContext:
    """Context passed to callback hooks for state access."""

    get_app_state: Callable[[], Any]  # Returns AppState
    update_attribution_state: Callable[[Callable[[Any], Any]], None]


# Type for hook callback function
# Using Any for optional params to avoid Python version compatibility issues
HookCallbackFn = Callable[..., Awaitable[HookJSONOutput]]


@dataclass
class HookCallback:
    """Hook that is a callback."""

    type: Literal["callback"] = "callback"
    callback: HookCallbackFn | None = None
    timeout: int | None = None
    internal: bool = False


@dataclass
class HookCallbackMatcher:
    """Matcher for hook callbacks."""

    hooks: list[HookCallback] = field(default_factory=list)
    matcher: str | None = None
    plugin_name: str | None = None


# ============================================================================
# Hook Progress and Error Types
# ============================================================================


@dataclass
class HookProgress:
    """Progress update from a hook."""

    type: Literal["hook_progress"] = "hook_progress"
    hook_event: HookEvent = "PreToolUse"
    hook_name: str = ""
    command: str = ""
    prompt_text: str | None = None
    status_message: str | None = None


@dataclass
class HookBlockingError:
    """A blocking error from a hook."""

    blocking_error: str
    command: str


# ============================================================================
# Permission Request Result
# ============================================================================


@dataclass
class PermissionRequestResultAllow:
    """Allow result for permission request."""

    behavior: Literal["allow"] = "allow"
    updated_input: dict[str, Any] | None = None
    updated_permissions: list[Any] | None = None  # list[PermissionUpdate]


@dataclass
class PermissionRequestResultDeny:
    """Deny result for permission request."""

    behavior: Literal["deny"] = "deny"
    message: str | None = None
    interrupt: bool = False


PermissionRequestResult = PermissionRequestResultAllow | PermissionRequestResultDeny


# ============================================================================
# Hook Result Types
# ============================================================================


@dataclass
class HookResult:
    """Result from executing a hook."""

    outcome: Literal["success", "blocking", "non_blocking_error", "cancelled"]
    message: Any | None = None  # Message type
    system_message: Any | None = None  # Message type
    blocking_error: HookBlockingError | None = None
    prevent_continuation: bool = False
    stop_reason: str | None = None
    permission_behavior: Literal["ask", "deny", "allow", "passthrough"] | None = None
    hook_permission_decision_reason: str | None = None
    additional_context: str | None = None
    initial_user_message: str | None = None
    updated_input: dict[str, Any] | None = None
    updated_mcp_tool_output: Any | None = None
    permission_request_result: PermissionRequestResult | None = None
    retry: bool = False


@dataclass
class AggregatedHookResult:
    """Aggregated result from multiple hooks."""

    message: Any | None = None  # Message type
    blocking_errors: list[HookBlockingError] | None = None
    prevent_continuation: bool = False
    stop_reason: str | None = None
    hook_permission_decision_reason: str | None = None
    permission_behavior: Literal["ask", "deny", "allow", "passthrough"] | None = None
    additional_contexts: list[str] | None = None
    initial_user_message: str | None = None
    updated_input: dict[str, Any] | None = None
    updated_mcp_tool_output: Any | None = None
    permission_request_result: PermissionRequestResult | None = None
    retry: bool = False
