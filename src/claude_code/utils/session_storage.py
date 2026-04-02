"""
Session storage utilities.

Handles session persistence and transcript management.

Migrated from: utils/sessionStorage.ts (5106 lines) - Core functionality
"""

from __future__ import annotations

import json
import os
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path
from typing import Any, Literal

from .debug import log_for_debugging
from .env_utils import get_claude_config_home_dir
from .json_utils import parse_jsonl, safe_json_stringify
from .log import log_error

# Constants
MAX_TOMBSTONE_REWRITE_BYTES = 50 * 1024 * 1024  # 50MB


MessageType = Literal["user", "assistant", "attachment", "system", "progress"]


@dataclass
class LogOption:
    """Options for a log/session entry."""

    session_id: str
    first_prompt: str | None = None
    summary: str | None = None
    custom_title: str | None = None
    agent_name: str | None = None
    created_at: str | None = None
    updated_at: str | None = None


@dataclass
class TranscriptEntry:
    """A single entry in a transcript."""

    type: MessageType
    uuid: str
    parent_uuid: str | None = None
    content: Any = None
    timestamp: str | None = None


def get_projects_dir() -> str:
    """Get the projects directory."""
    return os.path.join(get_claude_config_home_dir(), "projects")


def get_session_dir(session_id: str) -> str:
    """Get the directory for a specific session."""
    from .cwd import get_cwd

    cwd = get_cwd()
    sanitized = sanitize_path(cwd)
    return os.path.join(get_projects_dir(), sanitized, session_id)


def sanitize_path(path: str) -> str:
    """
    Sanitize a path for use as a directory name.

    Replaces path separators and special characters.
    """
    # Remove leading slash
    if path.startswith("/"):
        path = path[1:]

    # Replace separators
    sanitized = path.replace("/", "-").replace("\\", "-")

    # Remove any double dashes
    while "--" in sanitized:
        sanitized = sanitized.replace("--", "-")

    return sanitized


def is_transcript_message(entry: dict[str, Any]) -> bool:
    """
    Check if an entry is a transcript message.

    Transcript messages include user, assistant, attachment, and system.
    Progress messages are NOT transcript messages.
    """
    msg_type = entry.get("type")
    return msg_type in ("user", "assistant", "attachment", "system")


def is_chain_participant(entry: dict[str, Any]) -> bool:
    """Check if a message participates in the parentUuid chain."""
    return entry.get("type") != "progress"


def is_legacy_progress_entry(entry: Any) -> bool:
    """Check if an entry is a legacy progress entry."""
    return isinstance(entry, dict) and entry.get("type") == "progress" and isinstance(entry.get("uuid"), str)


def record_queue_operation(op: dict[str, Any]) -> None:
    """
    Persist or log a command-queue operation (enqueue/dequeue/remove).

    Migrated from: utils/sessionStorage.ts (recordQueueOperation).
    """
    log_for_debugging(f"queue-operation {op.get('operation')}: {op.get('content', '')!r}")


async def record_queue_operation_async(op: dict[str, Any]) -> None:
    """Async wrapper for environments that schedule I/O-backed queue logs."""
    record_queue_operation(op)


def get_transcript_path(session_id: str) -> str:
    """Get the path to a session's transcript file."""
    session_dir = get_session_dir(session_id)
    return os.path.join(session_dir, "transcript.jsonl")


def get_session_memory_summary_path(session_id: str) -> str:
    """
    Session memory notes file for the session (summary.md).

    Mirrors ``utils/permissions/filesystem.ts`` ``getSessionMemoryPath``:
    ``{projects}/{sanitized-cwd}/{sessionId}/session-memory/summary.md``.
    """
    session_dir = get_session_dir(session_id)
    mem_dir = os.path.join(session_dir, "session-memory")
    os.makedirs(mem_dir, exist_ok=True)
    return os.path.join(mem_dir, "summary.md")


def session_exists(session_id: str) -> bool:
    """Check if a session exists."""
    transcript_path = get_transcript_path(session_id)
    return os.path.isfile(transcript_path)


def create_session(session_id: str) -> None:
    """Create a new session directory."""
    session_dir = get_session_dir(session_id)
    os.makedirs(session_dir, exist_ok=True)


def append_to_transcript(
    session_id: str,
    entry: dict[str, Any],
) -> None:
    """
    Append an entry to a session's transcript.

    Args:
        session_id: The session ID
        entry: The entry to append
    """
    transcript_path = get_transcript_path(session_id)

    # Ensure directory exists
    os.makedirs(os.path.dirname(transcript_path), exist_ok=True)

    # Append the entry
    with open(transcript_path, "a", encoding="utf-8") as f:
        f.write(safe_json_stringify(entry) + "\n")


def save_agent_color(
    session_id: str,
    agent_color: str,
    *,
    transcript_path: str | None = None,
) -> None:
    """
    Persist session prompt-bar color to the transcript (mirrors saveAgentColor in sessionStorage.ts).

    ``agent_color`` may be a named color or the sentinel ``default`` for reset.
    """
    path = transcript_path or get_transcript_path(session_id)
    os.makedirs(os.path.dirname(path), exist_ok=True)
    entry = {
        "type": "agent-color",
        "agentColor": agent_color,
        "sessionId": session_id,
    }
    with open(path, "a", encoding="utf-8") as f:
        f.write(safe_json_stringify(entry) + "\n")


def load_transcript(session_id: str) -> list[dict[str, Any]]:
    """
    Load a session's transcript.

    Args:
        session_id: The session ID

    Returns:
        List of transcript entries
    """
    transcript_path = get_transcript_path(session_id)

    if not os.path.isfile(transcript_path):
        return []

    try:
        content = Path(transcript_path).read_text(encoding="utf-8")
        entries = parse_jsonl(content)

        # Filter to transcript messages
        return [e for e in entries if is_transcript_message(e)]
    except Exception as e:
        log_error(e)
        return []


def load_messages(session_id: str) -> list[dict[str, Any]]:
    """
    Load a session's messages.

    Args:
        session_id: The session ID

    Returns:
        List of messages (excluding non-transcript entries)
    """
    return load_transcript(session_id)


def save_messages(
    session_id: str,
    messages: list[dict[str, Any]],
) -> None:
    """
    Save messages to a session's transcript.

    Overwrites the existing transcript.

    Args:
        session_id: The session ID
        messages: The messages to save
    """
    transcript_path = get_transcript_path(session_id)

    # Ensure directory exists
    os.makedirs(os.path.dirname(transcript_path), exist_ok=True)

    # Write all messages
    with open(transcript_path, "w", encoding="utf-8") as f:
        for msg in messages:
            f.write(safe_json_stringify(msg) + "\n")


def list_sessions(project_dir: str | None = None) -> list[LogOption]:
    """
    List all sessions for a project.

    Args:
        project_dir: The project directory (defaults to cwd)

    Returns:
        List of session options sorted by update time
    """
    from .cwd import get_cwd

    if project_dir is None:
        project_dir = get_cwd()

    sanitized = sanitize_path(project_dir)
    sessions_dir = os.path.join(get_projects_dir(), sanitized)

    if not os.path.isdir(sessions_dir):
        return []

    sessions = []

    try:
        for entry in os.listdir(sessions_dir):
            session_path = os.path.join(sessions_dir, entry)
            if not os.path.isdir(session_path):
                continue

            transcript_path = os.path.join(session_path, "transcript.jsonl")
            if not os.path.isfile(transcript_path):
                continue

            # Get file times
            stat = os.stat(transcript_path)
            created_at = datetime.fromtimestamp(stat.st_ctime).isoformat()
            updated_at = datetime.fromtimestamp(stat.st_mtime).isoformat()

            # Try to get first prompt
            first_prompt = None
            try:
                with open(transcript_path, encoding="utf-8") as f:
                    first_line = f.readline()
                    if first_line:
                        first_entry = json.loads(first_line)
                        if first_entry.get("type") == "user":
                            content = first_entry.get("message", {}).get("content", "")
                            if isinstance(content, str):
                                first_prompt = content[:200]
            except Exception:
                pass

            sessions.append(
                LogOption(
                    session_id=entry,
                    first_prompt=first_prompt,
                    created_at=created_at,
                    updated_at=updated_at,
                )
            )
    except Exception as e:
        log_error(e)

    # Sort by update time (newest first)
    sessions.sort(key=lambda s: s.updated_at or "", reverse=True)

    return sessions


def delete_session(session_id: str) -> bool:
    """
    Delete a session.

    Args:
        session_id: The session ID

    Returns:
        True if deleted successfully
    """
    import shutil

    session_dir = get_session_dir(session_id)

    if not os.path.isdir(session_dir):
        return False

    try:
        shutil.rmtree(session_dir)
        return True
    except Exception as e:
        log_error(e)
        return False


def get_session_metadata(session_id: str) -> dict[str, Any]:
    """
    Get metadata for a session.

    Args:
        session_id: The session ID

    Returns:
        Session metadata dict
    """
    session_dir = get_session_dir(session_id)
    metadata_path = os.path.join(session_dir, "metadata.json")

    if not os.path.isfile(metadata_path):
        return {"session_id": session_id}

    try:
        content = Path(metadata_path).read_text(encoding="utf-8")
        return json.loads(content)
    except Exception as e:
        log_error(e)
        return {"session_id": session_id}


def save_session_metadata(
    session_id: str,
    metadata: dict[str, Any],
) -> None:
    """
    Save metadata for a session.

    Args:
        session_id: The session ID
        metadata: The metadata to save
    """
    session_dir = get_session_dir(session_id)
    os.makedirs(session_dir, exist_ok=True)

    metadata_path = os.path.join(session_dir, "metadata.json")

    try:
        with open(metadata_path, "w", encoding="utf-8") as f:
            json.dump(metadata, f, indent=2)
    except Exception as e:
        log_error(e)
