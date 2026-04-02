"""
UI hook logic ported to asyncio-friendly handlers (no React).

Includes batch 1 helpers under ``hooks/*.ts``, batch 2 (bridge, limits, progress),
and batch 3 (IDE, queue, tasks, voice, etc.).
"""

from __future__ import annotations

from .after_first_render import (
    should_exit_after_first_render_for_ant_benchmark,
    write_startup_time_and_exit,
)
from .agent_color_manager import (
    AGENT_COLOR_TO_THEME_COLOR,
    AGENT_COLORS,
    AgentColorName,
    get_agent_color,
    set_agent_color,
)
from .agent_progress import (
    AgentProgress,
    ProgressTracker,
    ToolActivity,
    create_progress_tracker,
    get_progress_update,
    get_token_count_from_tracker,
    update_progress_from_assistant_message,
)
from .api_key_verification import (
    ApiKeyVerificationDeps,
    ApiKeyVerificationState,
    initial_verification_status,
    verify_api_key_now,
)
from .assistant_history import (
    MAX_FILL_PAGES,
    PREFETCH_THRESHOLD_ROWS,
    SENTINEL_LOADING,
    SENTINEL_LOADING_FAILED,
    SENTINEL_START,
    page_events_to_messages,
)
from .auto_mode_unavailable_notification import wrapped_past_auto_slot
from .auto_scroll import AutoScrollState
from .away_summary import (
    BLUR_DELAY_MS,
    AwaySummaryTimerState,
    has_summary_since_last_user_turn,
)
from .background_task_navigation import (
    BackgroundNavKeyEvent,
    BackgroundNavOptions,
    clamp_teammate_selection_after_count_change,
    handle_background_task_keydown,
    step_teammate_selection,
)
from .blink import BLINK_INTERVAL_MS, blink_should_run, blink_visible
from .bridge_connection import (
    MAX_CONSECUTIVE_INIT_FAILURES,
    BridgeConnectionHandler,
)
from .bridge_status import BridgeStatusInfo, bridge_status_snapshot, get_bridge_status
from .cancel_request import (
    KILL_AGENTS_CONFIRM_WINDOW_MS,
    cancel_ctrl_c_active,
    cancel_escape_active,
    cancel_escape_context_active,
    filter_tasks_running_local_agent,
    parse_kill_agents_second_press,
)
from .claude_ai_limits import ClaudeAiLimitsHandler
from .clipboard_image_hint import (
    FOCUS_CHECK_DEBOUNCE_MS,
    HINT_COOLDOWN_MS,
    ClipboardImageHintState,
    hint_cooldown_blocks,
    mark_hint_shown,
    should_run_focus_regain_check,
)
from .clipboard_image_hint import (
    NOTIFICATION_KEY as CLIPBOARD_IMAGE_HINT_NOTIFICATION_KEY,
)
from .command_queue import CommandQueuePort, get_frozen_queue_snapshot
from .compact_warning import CompactWarningHandler, watch_compact_warning_suppression
from .connection_status import IdeConnectionResult, IdeStatus, ide_connection_status
from .copy_on_select import SelectionStateLike, maybe_copy_on_select_notification
from .debug_mode import DebugModeHandler
from .deferred_hook_messages import DeferredHookMessagesState
from .diff_data import (
    MAX_LINES_PER_FILE,
    DiffData,
    DiffFile,
    GitDiffResult,
    GitDiffStats,
    build_diff_data,
)
from .diff_in_ide import (
    compute_edits_from_contents,
    ide_rpc_is_diff_rejected,
    ide_rpc_is_file_saved,
    ide_rpc_is_tab_closed,
    ide_rpc_saved_new_content,
)
from .direct_connect import DirectConnectCallbacks, DirectConnectSessionState
from .double_press import DOUBLE_PRESS_TIMEOUT_MS, DoublePressController
from .dynamic_config import resolve_dynamic_config
from .effort_level import EffortLevelHandler
from .elapsed_time import format_elapsed_time_ms
from .error_recovery import ErrorRecoveryHandler
from .exit_on_ctrl_cd import ExitOnCtrlCdController, ExitState
from .file_history_snapshot_init import run_file_history_snapshot_init_once
from .file_suggestions import CHUNK_MS as FILE_SUGGESTION_CHUNK_MS
from .file_suggestions import CLAUDE_CONFIG_SUBDIRS
from .history_search import (
    HistorySearchMutableState,
    PromptInputMode,
    accept_history_match,
    cancel_history_search,
    close_history_reader,
    execute_history_search,
    get_mode_from_input,
    get_value_from_input,
    handle_history_backspace_when_empty,
    reset_history_search,
    search_history,
    start_history_search,
)
from .ide_at_mentioned import IdeAtMentioned, parse_at_mentioned_params
from .ide_log_event_forwarder import forward_ide_log_notification
from .ide_selection import IdeSelection, ide_selection_from_notification_params
from .inbox_poller import InboxPollerPort, run_inbox_poll_once
from .input_buffer import BufferEntry, InputBufferState
from .issue_flag_banner import (
    IssueFlagBannerState,
    has_friction_signal,
    is_session_container_compatible,
)
from .log_messages import (
    LogMessagesState,
    advance_log_messages_state,
    transcript_slice_plan,
)
from .mailbox_bridge import MailboxLike, on_mailbox_revision_idle
from .main_loop_model import resolve_main_loop_model, subscribe_growthbook_refresh
from .manage_plugins import (
    PluginLoadMetrics,
    notify_plugins_need_reload,
    run_initial_plugin_load_simple,
)
from .memory_usage import MemoryUsageInfo, memory_usage_from_heap
from .merged_clients import merge_clients
from .merged_commands import merge_commands
from .merged_tools import merge_mcp_tools
from .min_display_time import MinDisplayTimeController
from .notify_after_timeout import (
    has_recent_interaction,
    run_notify_after_idle_poll,
    time_since_last_interaction,
)
from .paste_handler import (
    join_paste_chunks,
    should_buffer_as_paste,
    split_paste_lines_for_image_paths,
)
from .permission_context import ResolveOnce, create_resolve_once
from .permission_logging import CODE_EDITING_TOOLS, is_code_editing_tool
from .pr_status import (
    INITIAL_PR_STATUS,
    PrFetchResult,
    PrReviewState,
    PrStatusMutableState,
    apply_pr_fetch,
    run_pr_status_poll_loop,
    should_update_pr_status,
)
from .prompt_suggestion import (
    PromptSuggestionState,
    log_prompt_suggestion_outcome,
    visible_suggestion,
)
from .queue_processor import (
    ProcessQueueResult,
    QueryGuardLike,
    QueuedCmd,
    is_main_thread_command,
    is_slash_command,
    maybe_process_queue,
    process_queue_if_ready,
    should_run_queue_processor,
)
from .remote_session import RemoteSessionCallbacks, RemoteSessionHandles
from .render_placeholder import PlaceholderRenderResult, render_placeholder
from .scheduled_tasks import (
    CronSchedulerLike,
    ScheduledTasksSession,
    format_cron_fire_time,
    start_scheduled_tasks_session,
)
from .search_input import UNHANDLED_SPECIAL_KEYS
from .session_backgrounding import (
    SessionBackgroundingDeps,
    handle_background_session_key,
    sync_foregrounded_local_agent_task,
)
from .settings_accessor import select_settings
from .settings_change import subscribe_settings_change
from .skill_improvement_survey import apply_skill_improvement_survey_selection
from .skills_change import (
    reload_commands_after_growthbook_memo_clear,
    reload_commands_after_skill_change,
)
from .ssh_session import SshSessionHandles
from .startup_notification import run_startup_notification_once
from .swarm_initialization import SwarmInitContext, run_swarm_initialization
from .swarm_permission_poller import (
    PermissionResponseCallback,
    SandboxPermissionResponseCallback,
    clear_all_pending_callbacks,
    has_permission_callback,
    has_sandbox_permission_callback,
    parse_permission_updates,
    process_mailbox_permission_response,
    process_sandbox_permission_response,
    register_permission_callback,
    register_sandbox_permission_callback,
    unregister_permission_callback,
)
from .task_list_watcher import (
    TaskListPort,
    TaskListTask,
    TaskListWatcherState,
    check_for_tasks,
    find_available_task,
    format_task_as_prompt,
)
from .tasks_v2 import (
    TaskLike,
    TasksV2Port,
    TasksV2Store,
    collapse_expanded_tasks_when_hidden,
    run_tasks_v2_refresh_loop,
)
from .teammate_lifecycle_notification import (
    diff_teammate_lifecycle_events,
    is_in_process_teammate_task,
    make_shutdown_notification,
    make_spawn_notification,
    parse_notification_count,
)
from .teammate_view_auto_exit import maybe_auto_exit_teammate_view
from .terminal_size import TerminalSize, require_terminal_size
from .text_input import TextInputDriverPlaceholder
from .timeout import TimeoutController
from .tool_permission_handlers import (
    BASH_TOOL_NAME,
    PERMISSION_DIALOG_GRACE_PERIOD_MS,
    permission_prompt_within_grace_period,
    run_coordinator_automated_permission_checks,
    run_swarm_worker_classifier_gate,
)
from .turn_diffs import (
    PatchHunk,
    TurnDiff,
    TurnDiffCache,
    TurnFileDiff,
    compute_turn_diffs,
)
from .unified_suggestions import SuggestionItemDict, coerce_suggestion_score
from .update_notification import (
    get_semver_part,
    next_update_notification_state,
    should_show_update_notification,
)
from .vim_input import VimInputDriverPlaceholder
from .virtual_scroll import (
    COLD_START_COUNT,
    DEFAULT_ESTIMATE,
    MAX_MOUNTED_ITEMS,
    OVERSCAN_ROWS,
    PESSIMISTIC_HEIGHT,
    SCROLL_QUANTUM,
    SLIDE_STEP,
)
from .voice import (
    AUDIO_LEVEL_BARS,
    DEFAULT_STT_LANGUAGE,
    FIRST_PRESS_FALLBACK_MS,
    FOCUS_SILENCE_TIMEOUT_MS,
    LANGUAGE_NAME_TO_CODE,
    RELEASE_TIMEOUT_MS,
    REPEAT_FALLBACK_MS,
    SUPPORTED_LANGUAGE_CODES,
    compute_level,
    normalize_language_for_stt,
)
from .voice_enabled import compute_voice_enabled
from .voice_keyterms import (
    GLOBAL_VOICE_KEYTERMS,
    MAX_VOICE_KEYTERMS,
    get_voice_keyterms,
    split_identifier,
)

__all__ = [
    "AGENT_COLORS",
    "AGENT_COLOR_TO_THEME_COLOR",
    "AUDIO_LEVEL_BARS",
    "AgentColorName",
    "AgentProgress",
    "AutoScrollState",
    "BackgroundNavKeyEvent",
    "BackgroundNavOptions",
    "BASH_TOOL_NAME",
    "BridgeConnectionHandler",
    "BridgeStatusInfo",
    "BufferEntry",
    "COLD_START_COUNT",
    "ClaudeAiLimitsHandler",
    "CompactWarningHandler",
    "CronSchedulerLike",
    "DEFAULT_ESTIMATE",
    "DEFAULT_STT_LANGUAGE",
    "DebugModeHandler",
    "EffortLevelHandler",
    "ErrorRecoveryHandler",
    "FIRST_PRESS_FALLBACK_MS",
    "FOCUS_SILENCE_TIMEOUT_MS",
    "GLOBAL_VOICE_KEYTERMS",
    "HistorySearchMutableState",
    "INITIAL_PR_STATUS",
    "IdeAtMentioned",
    "IdeConnectionResult",
    "IdeSelection",
    "IdeStatus",
    "InboxPollerPort",
    "InputBufferState",
    "IssueFlagBannerState",
    "LANGUAGE_NAME_TO_CODE",
    "LogMessagesState",
    "MAX_CONSECUTIVE_INIT_FAILURES",
    "MAX_MOUNTED_ITEMS",
    "MAX_VOICE_KEYTERMS",
    "MailboxLike",
    "MemoryUsageInfo",
    "MinDisplayTimeController",
    "OVERSCAN_ROWS",
    "PESSIMISTIC_HEIGHT",
    "PERMISSION_DIALOG_GRACE_PERIOD_MS",
    "PatchHunk",
    "PermissionResponseCallback",
    "PluginLoadMetrics",
    "PrFetchResult",
    "PrReviewState",
    "PrStatusMutableState",
    "ProcessQueueResult",
    "ProgressTracker",
    "PromptInputMode",
    "PromptSuggestionState",
    "QueryGuardLike",
    "QueuedCmd",
    "RELEASE_TIMEOUT_MS",
    "REPEAT_FALLBACK_MS",
    "RemoteSessionCallbacks",
    "RemoteSessionHandles",
    "SCROLL_QUANTUM",
    "SLIDE_STEP",
    "SandboxPermissionResponseCallback",
    "ScheduledTasksSession",
    "SelectionStateLike",
    "SessionBackgroundingDeps",
    "SUPPORTED_LANGUAGE_CODES",
    "SshSessionHandles",
    "SwarmInitContext",
    "TaskLike",
    "TaskListPort",
    "TaskListTask",
    "TaskListWatcherState",
    "TasksV2Port",
    "TasksV2Store",
    "TerminalSize",
    "TextInputDriverPlaceholder",
    "TimeoutController",
    "ToolActivity",
    "UNHANDLED_SPECIAL_KEYS",
    "accept_history_match",
    "advance_log_messages_state",
    "apply_pr_fetch",
    "apply_skill_improvement_survey_selection",
    "bridge_status_snapshot",
    "cancel_history_search",
    "check_for_tasks",
    "clamp_teammate_selection_after_count_change",
    "clear_all_pending_callbacks",
    "close_history_reader",
    "collapse_expanded_tasks_when_hidden",
    "compute_level",
    "compute_turn_diffs",
    "compute_voice_enabled",
    "create_progress_tracker",
    "execute_history_search",
    "find_available_task",
    "format_cron_fire_time",
    "format_task_as_prompt",
    "forward_ide_log_notification",
    "get_agent_color",
    "get_bridge_status",
    "get_mode_from_input",
    "get_progress_update",
    "get_semver_part",
    "get_token_count_from_tracker",
    "get_voice_keyterms",
    "get_value_from_input",
    "handle_background_session_key",
    "handle_background_task_keydown",
    "handle_history_backspace_when_empty",
    "has_friction_signal",
    "has_permission_callback",
    "has_recent_interaction",
    "has_sandbox_permission_callback",
    "ide_connection_status",
    "ide_selection_from_notification_params",
    "is_main_thread_command",
    "is_session_container_compatible",
    "is_slash_command",
    "join_paste_chunks",
    "log_prompt_suggestion_outcome",
    "maybe_auto_exit_teammate_view",
    "permission_prompt_within_grace_period",
    "maybe_copy_on_select_notification",
    "maybe_process_queue",
    "memory_usage_from_heap",
    "merge_clients",
    "merge_commands",
    "merge_mcp_tools",
    "next_update_notification_state",
    "normalize_language_for_stt",
    "notify_plugins_need_reload",
    "on_mailbox_revision_idle",
    "parse_at_mentioned_params",
    "parse_permission_updates",
    "process_mailbox_permission_response",
    "process_queue_if_ready",
    "process_sandbox_permission_response",
    "register_permission_callback",
    "register_sandbox_permission_callback",
    "reload_commands_after_growthbook_memo_clear",
    "reload_commands_after_skill_change",
    "require_terminal_size",
    "reset_history_search",
    "resolve_main_loop_model",
    "run_file_history_snapshot_init_once",
    "run_inbox_poll_once",
    "run_initial_plugin_load_simple",
    "run_notify_after_idle_poll",
    "run_pr_status_poll_loop",
    "run_swarm_initialization",
    "run_tasks_v2_refresh_loop",
    "run_coordinator_automated_permission_checks",
    "run_swarm_worker_classifier_gate",
    "search_history",
    "select_settings",
    "set_agent_color",
    "should_buffer_as_paste",
    "should_run_queue_processor",
    "should_show_update_notification",
    "should_update_pr_status",
    "split_paste_lines_for_image_paths",
    "start_history_search",
    "split_identifier",
    "start_scheduled_tasks_session",
    "step_teammate_selection",
    "subscribe_growthbook_refresh",
    "subscribe_settings_change",
    "sync_foregrounded_local_agent_task",
    "time_since_last_interaction",
    "transcript_slice_plan",
    "unregister_permission_callback",
    "update_progress_from_assistant_message",
    "visible_suggestion",
    "watch_compact_warning_suppression",
    "TurnDiff",
    "TurnDiffCache",
    "TurnFileDiff",
    "VimInputDriverPlaceholder",
    "ApiKeyVerificationDeps",
    "ApiKeyVerificationState",
    "AwaySummaryTimerState",
    "BLINK_INTERVAL_MS",
    "BLUR_DELAY_MS",
    "CLIPBOARD_IMAGE_HINT_NOTIFICATION_KEY",
    "ClipboardImageHintState",
    "CLAUDE_CONFIG_SUBDIRS",
    "CODE_EDITING_TOOLS",
    "CommandQueuePort",
    "DeferredHookMessagesState",
    "DiffData",
    "DiffFile",
    "DirectConnectCallbacks",
    "DirectConnectSessionState",
    "DOUBLE_PRESS_TIMEOUT_MS",
    "DoublePressController",
    "ExitOnCtrlCdController",
    "ExitState",
    "FILE_SUGGESTION_CHUNK_MS",
    "FOCUS_CHECK_DEBOUNCE_MS",
    "GitDiffResult",
    "GitDiffStats",
    "HINT_COOLDOWN_MS",
    "KILL_AGENTS_CONFIRM_WINDOW_MS",
    "MAX_FILL_PAGES",
    "MAX_LINES_PER_FILE",
    "PREFETCH_THRESHOLD_ROWS",
    "PlaceholderRenderResult",
    "ResolveOnce",
    "SuggestionItemDict",
    "SENTINEL_LOADING",
    "SENTINEL_LOADING_FAILED",
    "SENTINEL_START",
    "blink_should_run",
    "blink_visible",
    "build_diff_data",
    "cancel_ctrl_c_active",
    "cancel_escape_active",
    "cancel_escape_context_active",
    "coerce_suggestion_score",
    "compute_edits_from_contents",
    "create_resolve_once",
    "diff_teammate_lifecycle_events",
    "filter_tasks_running_local_agent",
    "format_elapsed_time_ms",
    "get_frozen_queue_snapshot",
    "has_summary_since_last_user_turn",
    "hint_cooldown_blocks",
    "ide_rpc_is_diff_rejected",
    "ide_rpc_is_file_saved",
    "ide_rpc_is_tab_closed",
    "ide_rpc_saved_new_content",
    "initial_verification_status",
    "is_code_editing_tool",
    "is_in_process_teammate_task",
    "make_shutdown_notification",
    "make_spawn_notification",
    "mark_hint_shown",
    "page_events_to_messages",
    "parse_kill_agents_second_press",
    "parse_notification_count",
    "render_placeholder",
    "resolve_dynamic_config",
    "run_startup_notification_once",
    "should_exit_after_first_render_for_ant_benchmark",
    "should_run_focus_regain_check",
    "verify_api_key_now",
    "wrapped_past_auto_slot",
    "write_startup_time_and_exit",
]
