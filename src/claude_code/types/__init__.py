"""
Type definitions for Claude Code.

This module contains all the core type definitions used throughout the application,
including branded ID types, permission types, hook types, and more.

Protobuf-shaped analytics event schemas (mirrors of ``types/generated/*.ts``) live in
``claude_code.types.generated``.
"""

from .command import (
    Command,
    CommandBase,
    LocalCommand,
    LocalCommandResult,
    PromptCommand,
    get_command_name,
    is_command_enabled,
)
from .hooks import (
    HookCallback,
    HookEvent,
    HookInput,
    HookJSONOutput,
    HookResult,
    is_hook_event,
)
from .ids import (
    AgentId,
    SessionId,
    as_agent_id,
    as_session_id,
    to_agent_id,
)
from .logs import (
    Entry,
    LogOption,
    SerializedMessage,
    TranscriptMessage,
    sort_logs,
)
from .message import (
    AssistantMessage,
    ContentBlock,
    Message,
    SystemMessage,
    TextBlock,
    ToolResultBlock,
    ToolUseBlock,
    UserMessage,
    count_tool_uses,
    extract_text_content,
    is_assistant_message,
    is_user_message,
)
from .permissions import (
    PermissionBehavior,
    PermissionDecision,
    PermissionMode,
    PermissionResult,
    PermissionRule,
    PermissionRuleSource,
    PermissionRuleValue,
    PermissionUpdate,
    ToolPermissionContext,
)
from .plugin import (
    LoadedPlugin,
    PluginError,
    PluginLoadResult,
    PluginManifest,
    get_plugin_error_message,
)
from .text_input import (
    PastedContent,
    PromptInputMode,
    QueuedCommand,
    QueuePriority,
    VimMode,
    is_valid_image_paste,
)

__all__ = [
    # ids
    "SessionId",
    "AgentId",
    "as_session_id",
    "as_agent_id",
    "to_agent_id",
    # permissions
    "PermissionMode",
    "PermissionBehavior",
    "PermissionRule",
    "PermissionRuleValue",
    "PermissionRuleSource",
    "PermissionUpdate",
    "PermissionDecision",
    "PermissionResult",
    "ToolPermissionContext",
    # hooks
    "HookEvent",
    "HookInput",
    "HookResult",
    "HookCallback",
    "HookJSONOutput",
    "is_hook_event",
    # logs
    "LogOption",
    "SerializedMessage",
    "TranscriptMessage",
    "Entry",
    "sort_logs",
    # command
    "Command",
    "CommandBase",
    "PromptCommand",
    "LocalCommand",
    "LocalCommandResult",
    "get_command_name",
    "is_command_enabled",
    # text_input
    "QueuedCommand",
    "QueuePriority",
    "PromptInputMode",
    "VimMode",
    "PastedContent",
    "is_valid_image_paste",
    # plugin
    "PluginManifest",
    "LoadedPlugin",
    "PluginError",
    "PluginLoadResult",
    "get_plugin_error_message",
    # message
    "Message",
    "UserMessage",
    "AssistantMessage",
    "SystemMessage",
    "TextBlock",
    "ToolUseBlock",
    "ToolResultBlock",
    "ContentBlock",
    "is_user_message",
    "is_assistant_message",
    "extract_text_content",
    "count_tool_uses",
]
