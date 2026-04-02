"""
Chat message utilities (``utils/messages.ts``) and system-init parity (``systemInit.ts``).

Core implementations live in :mod:`claude_code.utils.message_helpers` so this package
does not shadow a sibling ``messages.py`` module.
"""

from __future__ import annotations

from ..message_helpers import (
    CANCEL_MESSAGE,
    INTERRUPT_MESSAGE,
    INTERRUPT_MESSAGE_FOR_TOOL_USE,
    NO_RESPONSE_REQUESTED,
    PLAN_REJECTION_PREFIX,
    REJECT_MESSAGE,
    REJECT_MESSAGE_WITH_REASON_PREFIX,
    SUBAGENT_REJECT_MESSAGE,
    SUBAGENT_REJECT_MESSAGE_WITH_REASON_PREFIX,
    SYNTHETIC_MODEL,
    count_tool_use_blocks,
    create_assistant_api_error_message,
    create_assistant_message,
    create_attachment_message,
    create_compact_boundary_message,
    create_microcompact_boundary_message,
    create_system_message,
    create_tool_use_summary_message,
    create_user_interruption_message,
    create_user_message,
    derive_short_message_id,
    extract_text_content,
    extract_tool_use_ids,
    generate_uuid,
    get_assistant_message_text,
    get_content_text,
    get_last_assistant_message,
    get_messages_after_compact_boundary,
    is_compact_boundary_message,
    normalize_messages_for_api,
    strip_signature_blocks,
)
from .system_init import (
    SystemInitInputs,
    build_system_init_message,
    sdk_compat_tool_name,
)

__all__ = [
    "CANCEL_MESSAGE",
    "INTERRUPT_MESSAGE",
    "INTERRUPT_MESSAGE_FOR_TOOL_USE",
    "NO_RESPONSE_REQUESTED",
    "PLAN_REJECTION_PREFIX",
    "REJECT_MESSAGE",
    "REJECT_MESSAGE_WITH_REASON_PREFIX",
    "SUBAGENT_REJECT_MESSAGE",
    "SUBAGENT_REJECT_MESSAGE_WITH_REASON_PREFIX",
    "SYNTHETIC_MODEL",
    "SystemInitInputs",
    "build_system_init_message",
    "sdk_compat_tool_name",
    "count_tool_use_blocks",
    "create_assistant_api_error_message",
    "create_assistant_message",
    "create_attachment_message",
    "create_compact_boundary_message",
    "create_microcompact_boundary_message",
    "create_system_message",
    "create_tool_use_summary_message",
    "create_user_interruption_message",
    "create_user_message",
    "derive_short_message_id",
    "extract_text_content",
    "extract_tool_use_ids",
    "generate_uuid",
    "get_assistant_message_text",
    "get_content_text",
    "get_last_assistant_message",
    "get_messages_after_compact_boundary",
    "is_compact_boundary_message",
    "normalize_messages_for_api",
    "strip_signature_blocks",
]
