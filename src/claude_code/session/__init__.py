"""
Session Management.

Handles session storage, persistence, and restoration.
"""

from .storage import (
    SessionStorage,
    get_session_dir,
    get_sessions_root,
    load_messages,
    save_message,
)
from .types import (
    PersistedSession,
    SerializedMessage,
    TranscriptEntry,
)

__all__ = [
    # Storage
    "SessionStorage",
    "get_session_dir",
    "get_sessions_root",
    "save_message",
    "load_messages",
    # Types
    "SerializedMessage",
    "TranscriptEntry",
    "PersistedSession",
]
