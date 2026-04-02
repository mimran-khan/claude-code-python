"""
Global application state.

This module maintains global state for the Claude Code application.
DO NOT ADD MORE STATE HERE - BE JUDICIOUS WITH GLOBAL STATE.

Migrated from: bootstrap/state.ts (1759 lines)
"""

from __future__ import annotations

import contextlib
import os
import time
import uuid
from collections.abc import Callable
from dataclasses import dataclass, field
from typing import Any, Literal, Protocol

from ..types.ids import SessionId


class OtelEventEmitter(Protocol):
    """OpenTelemetry Logs API event logger (emit log records as events)."""

    def emit(self, record: Any) -> Any:
        """Emit a log record; may return an awaitable for async SDKs."""
        ...


_otel_event_logger: OtelEventEmitter | None = None


def get_otel_event_logger() -> OtelEventEmitter | None:
    """Event logger for `claude_code.*` OTEL events (mirrors TS getEventLogger)."""
    return _otel_event_logger


def set_otel_event_logger(logger: OtelEventEmitter | None) -> None:
    """Register the global OTEL event logger (set during telemetry init)."""
    global _otel_event_logger
    _otel_event_logger = logger


@dataclass
class ChannelEntry:
    """Entry for a channel server."""

    kind: Literal["plugin", "server"]
    name: str
    marketplace: str | None = None
    dev: bool = False


@dataclass
class ModelUsage:
    """Token usage for a model."""

    input_tokens: int = 0
    output_tokens: int = 0
    cache_read_input_tokens: int = 0
    cache_creation_input_tokens: int = 0
    web_search_requests: int = 0


@dataclass
class SessionCronTask:
    """A session-scoped cron task."""

    id: str
    cron: str
    prompt: str
    created_at: int
    recurring: bool = False
    agent_id: str | None = None


@dataclass
class InvokedSkillInfo:
    """Information about an invoked skill."""

    skill_name: str
    skill_path: str
    content: str
    invoked_at: int
    agent_id: str | None = None


@dataclass
class SlowOperation:
    """A slow operation for tracking."""

    operation: str
    duration_ms: int
    timestamp: int


@dataclass
class State:
    """Global application state."""

    # Directory state
    original_cwd: str = ""
    project_root: str = ""
    cwd: str = ""

    # Cost tracking
    total_cost_usd: float = 0.0
    total_api_duration: int = 0
    total_api_duration_without_retries: int = 0
    total_tool_duration: int = 0

    # Turn tracking
    turn_hook_duration_ms: int = 0
    turn_tool_duration_ms: int = 0
    turn_classifier_duration_ms: int = 0
    turn_tool_count: int = 0
    turn_hook_count: int = 0
    turn_classifier_count: int = 0

    # Timing
    start_time: int = field(default_factory=lambda: int(time.time() * 1000))
    last_interaction_time: int = field(default_factory=lambda: int(time.time() * 1000))

    # Lines changed tracking
    total_lines_added: int = 0
    total_lines_removed: int = 0
    has_unknown_model_cost: bool = False

    # Model usage
    model_usage: dict[str, ModelUsage] = field(default_factory=dict)
    main_loop_model_override: str | None = None
    initial_main_loop_model: str | None = None
    model_strings: dict[str, Any] | None = None

    # Session state
    is_interactive: bool = False
    kairos_active: bool = False
    strict_tool_result_pairing: bool = False
    sdk_agent_progress_summaries_enabled: bool = False
    user_msg_opt_in: bool = False
    client_type: str = "cli"
    session_source: str | None = None
    question_preview_format: Literal["markdown", "html"] | None = None

    # Settings
    flag_settings_path: str | None = None
    flag_settings_inline: dict[str, Any] | None = None
    allowed_setting_sources: list[str] = field(
        default_factory=lambda: [
            "userSettings",
            "projectSettings",
            "localSettings",
            "flagSettings",
            "policySettings",
        ]
    )

    # Tokens
    session_ingress_token: str | None = None
    oauth_token_from_fd: str | None = None
    api_key_from_fd: str | None = None

    # Session ID
    session_id: SessionId = field(default_factory=lambda: SessionId(str(uuid.uuid4())))
    parent_session_id: SessionId | None = None

    # Error log
    in_memory_error_log: list[dict[str, str]] = field(default_factory=list)

    # Plugins
    inline_plugins: list[str] = field(default_factory=list)
    chrome_flag_override: bool | None = None
    use_cowork_plugins: bool = False

    # Session flags
    session_bypass_permissions_mode: bool = False
    scheduled_tasks_enabled: bool = False
    session_cron_tasks: list[SessionCronTask] = field(default_factory=list)
    session_created_teams: set[str] = field(default_factory=set)
    session_trust_accepted: bool = False
    session_persistence_disabled: bool = False

    # Plan mode tracking
    has_exited_plan_mode: bool = False
    needs_plan_mode_exit_attachment: bool = False
    needs_auto_mode_exit_attachment: bool = False
    lsp_recommendation_shown_this_session: bool = False

    # SDK state
    init_json_schema: dict[str, Any] | None = None
    registered_hooks: dict[str, list[Any]] | None = None

    # Caches
    plan_slug_cache: dict[str, str] = field(default_factory=dict)
    invoked_skills: dict[str, InvokedSkillInfo] = field(default_factory=dict)
    slow_operations: list[SlowOperation] = field(default_factory=list)
    system_prompt_section_cache: dict[str, str | None] = field(default_factory=dict)

    # SDK betas
    sdk_betas: list[str] | None = None

    # Agent state
    main_thread_agent_type: str | None = None
    is_remote_mode: bool = False
    direct_connect_server_url: str | None = None

    # Date tracking
    last_emitted_date: str | None = None

    # Additional directories
    additional_directories_for_claude_md: list[str] = field(default_factory=list)

    # Channels
    allowed_channels: list[ChannelEntry] = field(default_factory=list)
    has_dev_channels: bool = False
    session_project_dir: str | None = None

    # Prompt cache
    prompt_cache_1h_allowlist: list[str] | None = None
    prompt_cache_1h_eligible: bool | None = None

    # Beta header latches
    afk_mode_header_latched: bool | None = None
    fast_mode_header_latched: bool | None = None
    cache_editing_header_latched: bool | None = None
    thinking_clear_latched: bool | None = None

    # Prompt tracking
    prompt_id: str | None = None
    last_main_request_id: str | None = None
    last_api_completion_timestamp: int | None = None
    pending_post_compaction: bool = False


def _get_initial_state() -> State:
    """Create the initial state."""
    resolved_cwd = os.getcwd()
    with contextlib.suppress(Exception):
        resolved_cwd = os.path.realpath(resolved_cwd)

    return State(
        original_cwd=resolved_cwd,
        project_root=resolved_cwd,
        cwd=resolved_cwd,
    )


# Global state instance
_STATE = _get_initial_state()

# Session switch signal subscribers
_session_switch_subscribers: list[Callable[[SessionId], None]] = []


def get_session_id() -> SessionId:
    """Get the current session ID."""
    return _STATE.session_id


def is_session_persistence_disabled() -> bool:
    """True when session disk persistence is disabled for this process."""
    return _STATE.session_persistence_disabled


def get_sdk_betas() -> list[str] | None:
    """Beta feature flags active for the SDK stream."""
    return _STATE.sdk_betas


def regenerate_session_id(*, set_current_as_parent: bool = False) -> SessionId:
    """
    Regenerate the session ID.

    Args:
        set_current_as_parent: If True, set current session as parent.

    Returns:
        The new session ID.
    """
    if set_current_as_parent:
        _STATE.parent_session_id = _STATE.session_id

    # Drop the outgoing session's plan-slug entry
    _STATE.plan_slug_cache.pop(str(_STATE.session_id), None)

    _STATE.session_id = SessionId(str(uuid.uuid4()))
    _STATE.session_project_dir = None
    return _STATE.session_id


def get_parent_session_id() -> SessionId | None:
    """Get the parent session ID."""
    return _STATE.parent_session_id


def switch_session(
    session_id: SessionId,
    project_dir: str | None = None,
) -> None:
    """
    Switch the active session.

    Args:
        session_id: The new session ID.
        project_dir: Directory containing the session transcript.
    """
    _STATE.plan_slug_cache.pop(str(_STATE.session_id), None)
    _STATE.session_id = session_id
    _STATE.session_project_dir = project_dir

    for subscriber in _session_switch_subscribers:
        subscriber(session_id)


def on_session_switch(callback: Callable[[SessionId], None]) -> Callable[[], None]:
    """
    Register a callback for session switches.

    Args:
        callback: Function to call on session switch.

    Returns:
        Unsubscribe function.
    """
    _session_switch_subscribers.append(callback)

    def unsubscribe() -> None:
        _session_switch_subscribers.remove(callback)

    return unsubscribe


def get_session_project_dir() -> str | None:
    """Get the session project directory."""
    return _STATE.session_project_dir


def get_original_cwd() -> str:
    """Get the original working directory."""
    return _STATE.original_cwd


def get_project_root() -> str:
    """
    Get the stable project root directory.

    Unlike get_original_cwd(), this is never updated by mid-session tools.
    """
    return _STATE.project_root


def set_original_cwd(cwd: str) -> None:
    """Set the original working directory."""
    _STATE.original_cwd = cwd


def set_project_root(cwd: str) -> None:
    """
    Set the project root.

    Only for --worktree startup flag. Mid-session tools must NOT call this.
    """
    _STATE.project_root = cwd


def get_cwd_state() -> str:
    """Get the current working directory state."""
    return _STATE.cwd


def set_cwd_state(cwd: str) -> None:
    """Set the current working directory state."""
    _STATE.cwd = cwd


def get_direct_connect_server_url() -> str | None:
    """Get the direct connect server URL."""
    return _STATE.direct_connect_server_url


def set_direct_connect_server_url(url: str) -> None:
    """Set the direct connect server URL."""
    _STATE.direct_connect_server_url = url


def add_to_total_duration_state(duration: int, duration_without_retries: int) -> None:
    """Add to the total API duration."""
    _STATE.total_api_duration += duration
    _STATE.total_api_duration_without_retries += duration_without_retries


def add_to_total_cost_state(
    cost: float,
    model_usage: ModelUsage,
    model: str,
) -> None:
    """Add to the total cost."""
    _STATE.model_usage[model] = model_usage
    _STATE.total_cost_usd += cost


def get_total_cost_usd() -> float:
    """Get the total cost in USD."""
    return _STATE.total_cost_usd


def get_total_api_duration() -> int:
    """Get the total API duration."""
    return _STATE.total_api_duration


def get_total_duration() -> int:
    """Get the total session duration."""
    return int(time.time() * 1000) - _STATE.start_time


def get_total_api_duration_without_retries() -> int:
    """Get the total API duration without retries."""
    return _STATE.total_api_duration_without_retries


def get_total_tool_duration() -> int:
    """Get the total tool duration."""
    return _STATE.total_tool_duration


def add_to_tool_duration(duration: int) -> None:
    """Add to the tool duration."""
    _STATE.total_tool_duration += duration
    _STATE.turn_tool_duration_ms += duration
    _STATE.turn_tool_count += 1


def add_to_total_lines_changed(added: int, removed: int) -> None:
    """Add to the total lines changed."""
    _STATE.total_lines_added += added
    _STATE.total_lines_removed += removed


def get_total_lines_added() -> int:
    """Get the total lines added."""
    return _STATE.total_lines_added


def get_total_lines_removed() -> int:
    """Get the total lines removed."""
    return _STATE.total_lines_removed


def get_model_usage() -> dict[str, ModelUsage]:
    """Get model usage."""
    return _STATE.model_usage


def get_main_loop_model_override() -> str | None:
    """Get the model override set from CLI or config."""
    return _STATE.main_loop_model_override


def set_main_loop_model_override(model: str | None) -> None:
    """Set the main loop model override."""
    _STATE.main_loop_model_override = model


def get_is_interactive() -> bool:
    """Check if the session is interactive."""
    return _STATE.is_interactive


def get_is_non_interactive_session() -> bool:
    """True for headless / SDK streams (mirrors TS getIsNonInteractiveSession)."""
    return not _STATE.is_interactive


def set_is_interactive(value: bool) -> None:
    """Set the interactive flag."""
    _STATE.is_interactive = value


def get_kairos_active() -> bool:
    """True when Kairos mode is active (mirrors TS getKairosActive)."""
    return _STATE.kairos_active


def set_user_msg_opt_in(value: bool) -> None:
    """Couples brief-only / user-message opt-in (mirrors TS setUserMsgOptIn)."""
    _STATE.user_msg_opt_in = value


def get_user_msg_opt_in() -> bool:
    """Whether brief-mode user opt-in is set (mirrors TS userMsgOptIn read paths)."""
    return _STATE.user_msg_opt_in


def get_client_type() -> str:
    """Get the client type."""
    return _STATE.client_type


def get_use_cowork_plugins() -> bool:
    """True when session or env requests cowork_plugins layout (mirrors TS)."""
    if _STATE.use_cowork_plugins:
        return True
    v = os.environ.get("CLAUDE_CODE_USE_COWORK_PLUGINS")
    if not v:
        return False
    return str(v).lower().strip() in ("1", "true", "yes", "on")


def set_use_cowork_plugins(value: bool) -> None:
    """Set cowork plugins mode from CLI (e.g. --cowork)."""
    _STATE.use_cowork_plugins = value


def get_inline_plugins() -> list[str]:
    """Session plugin directories from --plugin-dir / SDK."""
    return list(_STATE.inline_plugins)


def set_inline_plugins(paths: list[str]) -> None:
    """Replace inline plugin paths."""
    _STATE.inline_plugins = list(paths)


def set_client_type(client_type: str) -> None:
    """Set the client type."""
    _STATE.client_type = client_type


def get_additional_directories_for_claude_md() -> list[str]:
    """Directories added via --add-dir / session state (mirrors TS)."""
    return list(_STATE.additional_directories_for_claude_md)


MAX_SLOW_OPERATIONS = 10
SLOW_OPERATION_TTL_MS = 10_000


def add_slow_operation(operation: str, duration_ms: int) -> None:
    """Record a slow operation for dev diagnostics (ANT builds in TS)."""
    if os.environ.get("USER_TYPE") != "ant":
        return
    if "exec" in operation and "claude-prompt-" in operation:
        return
    now = int(time.time() * 1000)
    _STATE.slow_operations = [op for op in _STATE.slow_operations if now - op.timestamp < SLOW_OPERATION_TTL_MS]
    _STATE.slow_operations.append(SlowOperation(operation=operation, duration_ms=duration_ms, timestamp=now))
    if len(_STATE.slow_operations) > MAX_SLOW_OPERATIONS:
        _STATE.slow_operations = _STATE.slow_operations[-MAX_SLOW_OPERATIONS:]


def get_slow_operations() -> tuple[SlowOperation, ...]:
    """Return a snapshot of recent slow operations."""
    return tuple(_STATE.slow_operations)


def set_has_unknown_model_cost() -> None:
    """Mark that an unknown model was used for cost calculation (analytics)."""
    _STATE.has_unknown_model_cost = True


def reset_cost_state() -> None:
    """Reset cost tracking state."""
    _STATE.total_cost_usd = 0.0
    _STATE.total_api_duration = 0
    _STATE.total_api_duration_without_retries = 0
    _STATE.total_tool_duration = 0
    _STATE.start_time = int(time.time() * 1000)
    _STATE.total_lines_added = 0
    _STATE.total_lines_removed = 0
    _STATE.has_unknown_model_cost = False
    _STATE.model_usage = {}
    _STATE.prompt_id = None


def add_to_in_memory_error_log(error: str, timestamp: str) -> None:
    """Add an error to the in-memory log."""
    MAX_IN_MEMORY_ERRORS = 100
    if len(_STATE.in_memory_error_log) >= MAX_IN_MEMORY_ERRORS:
        _STATE.in_memory_error_log.pop(0)
    _STATE.in_memory_error_log.append({"error": error, "timestamp": timestamp})


def get_prompt_id() -> str | None:
    """Get the current prompt ID."""
    return _STATE.prompt_id


def set_prompt_id(prompt_id: str | None) -> None:
    """Set the current prompt ID."""
    _STATE.prompt_id = prompt_id


def register_hook_callbacks(hooks: dict[str, list[Any]]) -> None:
    """
    Merge hook matchers into global registered hooks (mirrors TS registerHookCallbacks).
    Multiple calls append per event rather than replacing.
    """
    if _STATE.registered_hooks is None:
        _STATE.registered_hooks = {}
    for event, matchers in hooks.items():
        if not matchers:
            continue
        if event not in _STATE.registered_hooks:
            _STATE.registered_hooks[event] = []
        _STATE.registered_hooks[event].extend(matchers)


def get_registered_hooks() -> dict[str, list[Any]] | None:
    """Return the current hook registry, or None if never initialized."""
    return _STATE.registered_hooks


def clear_registered_hooks() -> None:
    """Clear all registered hooks (SDK + plugin)."""
    _STATE.registered_hooks = None


def clear_registered_plugin_hooks() -> None:
    """
    Remove plugin-originated matchers; keep callback hooks without pluginRoot.
    Mirrors TS clearRegisteredPluginHooks.
    """
    if not _STATE.registered_hooks:
        return
    filtered: dict[str, list[Any]] = {}
    for event, matchers in _STATE.registered_hooks.items():
        kept: list[Any] = []
        for m in matchers:
            if isinstance(m, dict) and ("pluginRoot" in m or "plugin_root" in m):
                continue
            if hasattr(m, "plugin_root") or hasattr(m, "pluginRoot"):
                continue
            kept.append(m)
        if kept:
            filtered[event] = kept
    _STATE.registered_hooks = filtered if filtered else None


def get_system_prompt_section_cache() -> dict[str, str | None]:
    """Return the system prompt section cache (name -> computed value)."""
    return _STATE.system_prompt_section_cache


def set_system_prompt_section_cache_entry(name: str, value: str | None) -> None:
    """Store a resolved system prompt section in the cache."""
    _STATE.system_prompt_section_cache[name] = value


def clear_system_prompt_section_state() -> None:
    """Clear cached system prompt sections (e.g. on /clear, /compact)."""
    _STATE.system_prompt_section_cache.clear()


def clear_beta_header_latches() -> None:
    """Reset beta header latches so a fresh conversation re-evaluates headers."""
    _STATE.afk_mode_header_latched = None
    _STATE.fast_mode_header_latched = None
    _STATE.cache_editing_header_latched = None
    _STATE.thinking_clear_latched = None


def reset_state_for_tests() -> None:
    """Reset state for tests. Only works in test environment."""
    global _STATE
    if os.environ.get("PYTEST_CURRENT_TEST") is None:
        raise RuntimeError("reset_state_for_tests can only be called in tests")

    _STATE = _get_initial_state()
    _session_switch_subscribers.clear()
