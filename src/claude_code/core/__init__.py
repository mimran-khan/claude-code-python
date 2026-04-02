"""Core module containing QueryEngine, Tool, and related base classes."""

from .context import (
    get_git_status,
    get_system_context,
    get_system_prompt_injection,
    get_user_context,
    set_system_prompt_injection,
)
from .query_engine import (
    QueryEngine,
    QueryEngineConfig,
)
from .tool import (
    CompactProgressEvent,
    Progress,
    QueryChainTracking,
    Tool,
    ToolCallProgress,
    ToolInputJSONSchema,
    ToolPermissionContext,
    ToolProgress,
    ToolProgressData,
    ToolResult,
    Tools,
    ToolUseContext,
    ValidationResult,
    filter_tool_progress_messages,
    get_empty_tool_permission_context,
    tool_matches_name,
)

__all__ = [
    # tool
    "ToolInputJSONSchema",
    "QueryChainTracking",
    "ValidationResult",
    "ToolPermissionContext",
    "get_empty_tool_permission_context",
    "CompactProgressEvent",
    "ToolUseContext",
    "ToolProgressData",
    "Progress",
    "ToolProgress",
    "filter_tool_progress_messages",
    "ToolResult",
    "ToolCallProgress",
    "tool_matches_name",
    "Tool",
    "Tools",
    # query_engine
    "QueryEngineConfig",
    "QueryEngine",
    # context
    "get_system_prompt_injection",
    "set_system_prompt_injection",
    "get_git_status",
    "get_user_context",
    "get_system_context",
]
