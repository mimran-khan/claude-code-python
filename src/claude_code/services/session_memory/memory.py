"""
Session memory implementation.

Background extraction and maintenance of session notes.

Migrated from: services/SessionMemory/sessionMemory.ts (496 lines)
"""

from __future__ import annotations

import contextlib
import os
from dataclasses import dataclass
from typing import Any

from .utils import DEFAULT_SESSION_MEMORY_CONFIG


@dataclass
class SessionMemory:
    """
    Session memory state.

    Automatically maintained notes about the current conversation.
    """

    content: str = ""
    last_updated: float | None = None
    message_count: int = 0
    token_count: int = 0
    initialized: bool = False


# Module state
_session_memory = SessionMemory()
_config = DEFAULT_SESSION_MEMORY_CONFIG
_memory_path: str | None = None


def is_session_memory_enabled() -> bool:
    """
    Check if session memory is enabled.

    Returns:
        True if enabled
    """
    from ...utils.env_utils import is_env_truthy

    # Check environment override
    if is_env_truthy(os.getenv("CLAUDE_CODE_DISABLE_SESSION_MEMORY")):
        return False

    # Feature gate would be checked here
    return True


def get_session_memory_path() -> str | None:
    """
    Get the path to the session memory file.

    Returns:
        Path or None if not available
    """
    global _memory_path

    if _memory_path:
        return _memory_path

    # Get session memory directory
    home = os.path.expanduser("~")
    memory_dir = os.path.join(home, ".claude", "memory")

    # Create if needed
    os.makedirs(memory_dir, exist_ok=True)

    # Generate session-specific filename
    import uuid

    session_id = os.getenv("CLAUDE_CODE_SESSION_ID", str(uuid.uuid4())[:8])
    _memory_path = os.path.join(memory_dir, f"session_{session_id}.md")

    return _memory_path


def get_session_memory() -> SessionMemory:
    """
    Get the current session memory.

    Returns:
        SessionMemory instance
    """
    return _session_memory


async def update_session_memory(
    messages: list[dict[str, Any]],
    force: bool = False,
) -> bool:
    """
    Update session memory based on conversation.

    Args:
        messages: Conversation messages
        force: Force update even if thresholds not met

    Returns:
        True if updated
    """
    global _session_memory

    if not is_session_memory_enabled():
        return False

    from .utils import has_met_update_threshold

    if not force and not has_met_update_threshold(messages, _config):
        return False

    # Extract key information from messages
    content = _extract_session_notes(messages)

    import time

    _session_memory = SessionMemory(
        content=content,
        last_updated=time.time(),
        message_count=len(messages),
        initialized=True,
    )

    # Write to file
    path = get_session_memory_path()
    if path:
        try:
            with open(path, "w") as f:
                f.write(content)
        except OSError:
            pass

    return True


def _extract_session_notes(messages: list[dict[str, Any]]) -> str:
    """
    Extract key notes from conversation.

    Args:
        messages: Conversation messages

    Returns:
        Markdown notes
    """
    lines = ["# Session Notes", ""]

    # Track key information
    files_touched: set[str] = set()
    tools_used: dict[str, int] = {}
    topics: list[str] = []

    for msg in messages:
        role = msg.get("role", "")
        content = msg.get("content", [])

        if isinstance(content, list):
            for block in content:
                block_type = block.get("type", "")

                # Track tool use
                if block_type == "tool_use":
                    tool_name = block.get("name", "unknown")
                    tools_used[tool_name] = tools_used.get(tool_name, 0) + 1

                    # Extract file paths from tool inputs
                    tool_input = block.get("input", {})
                    if isinstance(tool_input, dict):
                        path = tool_input.get("path") or tool_input.get("file_path")
                        if path:
                            files_touched.add(path)

                # Extract topics from user messages
                if role == "user" and block_type == "text":
                    text = block.get("text", "")
                    if text and len(text) > 20:
                        first_line = text.split("\n")[0][:100]
                        if first_line not in topics:
                            topics.append(first_line)

    # Format notes
    if topics:
        lines.append("## Topics Discussed")
        for topic in topics[:10]:
            lines.append(f"- {topic}")
        lines.append("")

    if files_touched:
        lines.append("## Files Touched")
        for path in sorted(files_touched)[:20]:
            lines.append(f"- `{path}`")
        lines.append("")

    if tools_used:
        lines.append("## Tools Used")
        for tool, count in sorted(tools_used.items(), key=lambda x: -x[1])[:10]:
            lines.append(f"- {tool}: {count} times")
        lines.append("")

    return "\n".join(lines)


async def load_session_memory(path: str | None = None) -> str | None:
    """
    Load session memory from file.

    Args:
        path: Optional path to load from

    Returns:
        Memory content or None
    """
    global _session_memory

    path = path or get_session_memory_path()
    if not path or not os.path.exists(path):
        return None

    try:
        with open(path) as f:
            content = f.read()

        _session_memory.content = content
        _session_memory.initialized = True
        return content
    except OSError:
        return None


def clear_session_memory() -> None:
    """Clear the current session memory."""
    global _session_memory
    _session_memory = SessionMemory()

    path = get_session_memory_path()
    if path and os.path.exists(path):
        with contextlib.suppress(OSError):
            os.remove(path)
