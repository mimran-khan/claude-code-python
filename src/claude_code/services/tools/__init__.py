"""
Tool services module.

Provides tool execution, orchestration, and hook management.

Migrated from: services/tools/*.ts
"""

from .execution import (
    ToolExecutionContext,
    ToolExecutionResult,
    classify_tool_error,
    execute_tool,
    execute_tool_with_hooks,
)
from .utils import (
    get_tool_use_id_from_parent_message,
    tag_messages_with_tool_use_id,
)

__all__ = [
    "ToolExecutionResult",
    "ToolExecutionContext",
    "execute_tool",
    "execute_tool_with_hooks",
    "classify_tool_error",
    "tag_messages_with_tool_use_id",
    "get_tool_use_id_from_parent_message",
    "StreamingToolExecutor",
    "ToolStatus",
    "TrackedTool",
    "MessageUpdate",
    "run_tools",
    "get_max_tool_use_concurrency",
    "run_post_tool_use_hooks",
    "run_pre_tool_hooks",
]
