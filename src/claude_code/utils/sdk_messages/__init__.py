"""
SDK `system/init` and message wire-format mappers.

Migrated from: utils/messages/*.ts (Python package name avoids clash with utils.messages).
"""

from .mappers import (
    from_sdk_compact_metadata,
    local_command_output_to_sdk_assistant_message,
    to_internal_messages,
    to_sdk_compact_metadata,
    to_sdk_messages,
    to_sdk_rate_limit_info,
)
from .system_init import SystemInitInputs, build_system_init_message, sdk_compat_tool_name

__all__ = [
    "SystemInitInputs",
    "build_system_init_message",
    "sdk_compat_tool_name",
    "from_sdk_compact_metadata",
    "local_command_output_to_sdk_assistant_message",
    "to_internal_messages",
    "to_sdk_compact_metadata",
    "to_sdk_messages",
    "to_sdk_rate_limit_info",
]
