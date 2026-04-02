"""Context compaction services."""

from .api_microcompact import (
    ContextManagementConfig,
    get_api_context_management,
)
from .auto_compact import (
    auto_compact_if_needed,
    get_auto_compact_threshold,
)
from .compact import (
    CompactConfig,
    CompactResult,
    compact_messages,
    should_compact,
)
from .compact_warning_state import (
    clear_compact_warning_suppression,
    is_compact_warning_suppressed,
    suppress_compact_warning,
)
from .grouping import group_messages_by_api_round
from .post_compact_cleanup import run_post_compact_cleanup
from .session_memory_compact import (
    DEFAULT_SM_COMPACT_CONFIG,
    SessionMemoryCompactConfig,
    adjust_index_to_preserve_api_invariants,
    calculate_messages_to_keep_index,
    get_session_memory_compact_config,
    has_text_blocks,
    init_session_memory_compact_config,
    reset_session_memory_compact_config,
    set_session_memory_compact_config,
    should_use_session_memory_compaction,
    try_session_memory_compaction,
)
from .time_based_mc_config import TimeBasedMCConfig, get_time_based_mc_config
from .token_utils import (
    estimate_message_tokens,
    estimate_messages_tokens,
    estimate_text_tokens,
    message_to_text,
)

__all__ = [
    "compact_messages",
    "should_compact",
    "CompactConfig",
    "CompactResult",
    "auto_compact_if_needed",
    "get_auto_compact_threshold",
    "ContextManagementConfig",
    "get_api_context_management",
    "suppress_compact_warning",
    "clear_compact_warning_suppression",
    "is_compact_warning_suppressed",
    "group_messages_by_api_round",
    "run_post_compact_cleanup",
    "TimeBasedMCConfig",
    "get_time_based_mc_config",
    "estimate_text_tokens",
    "estimate_message_tokens",
    "estimate_messages_tokens",
    "message_to_text",
    # Session memory compact (sessionMemoryCompact.ts)
    "DEFAULT_SM_COMPACT_CONFIG",
    "SessionMemoryCompactConfig",
    "init_session_memory_compact_config",
    "adjust_index_to_preserve_api_invariants",
    "calculate_messages_to_keep_index",
    "get_session_memory_compact_config",
    "has_text_blocks",
    "reset_session_memory_compact_config",
    "set_session_memory_compact_config",
    "should_use_session_memory_compaction",
    "try_session_memory_compaction",
]
