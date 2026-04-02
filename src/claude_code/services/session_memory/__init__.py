"""
Session Memory service.

Automatically maintains notes about the conversation.

Migrated from: services/SessionMemory/*.ts (3 files)
"""

from .memory import (
    SessionMemory,
    get_session_memory,
    get_session_memory_path,
    is_session_memory_enabled,
    update_session_memory,
)
from .utils import (
    DEFAULT_SESSION_MEMORY_CONFIG,
    SessionMemoryConfig,
    get_tool_calls_between_updates,
    has_met_initialization_threshold,
    has_met_update_threshold,
)

__all__ = [
    # Memory
    "SessionMemory",
    "SessionMemoryConfig",
    "get_session_memory",
    "update_session_memory",
    "is_session_memory_enabled",
    "get_session_memory_path",
    # Utils
    "DEFAULT_SESSION_MEMORY_CONFIG",
    "has_met_initialization_threshold",
    "has_met_update_threshold",
    "get_tool_calls_between_updates",
]
