"""
History management for prompt history.

This module handles reading and writing prompt history, including
support for pasted content storage and retrieval.

Migrated from: history.ts (465 lines)
"""

from __future__ import annotations

import asyncio
import json
import os
import re
import time
from collections.abc import AsyncIterator
from dataclasses import dataclass, field
from typing import TypedDict

from .bootstrap.state import get_project_root, get_session_id
from .utils.debug import log_for_debugging
from .utils.env import get_claude_config_home_dir, is_env_truthy

MAX_HISTORY_ITEMS = 100
MAX_PASTED_CONTENT_LENGTH = 1024


@dataclass
class PastedContent:
    """Content that was pasted into a prompt."""

    id: int
    type: str  # 'text' or 'image'
    content: str = ""
    media_type: str | None = None
    filename: str | None = None


@dataclass
class StoredPastedContent:
    """Stored paste content with optional hash reference."""

    id: int
    type: str
    content: str | None = None
    content_hash: str | None = None
    media_type: str | None = None
    filename: str | None = None


@dataclass
class HistoryEntry:
    """An entry in the prompt history."""

    display: str
    pasted_contents: dict[int, PastedContent] = field(default_factory=dict)


@dataclass
class LogEntry:
    """Internal log entry format."""

    display: str
    pasted_contents: dict[int, StoredPastedContent]
    timestamp: float
    project: str
    session_id: str | None = None


class ParsedReference(TypedDict):
    """A paste/image reference substring matched in prompt text."""

    id: int
    match: str
    index: int


@dataclass
class TimestampedHistoryEntry:
    """History entry with timestamp for ctrl+r picker."""

    display: str
    timestamp: float
    _log_entry: LogEntry

    async def resolve(self) -> HistoryEntry:
        """Resolve the full history entry."""
        return await _log_entry_to_history_entry(self._log_entry)


def get_pasted_text_ref_num_lines(text: str) -> int:
    """Get the number of newlines in pasted text."""
    return len(re.findall(r"\r\n|\r|\n", text))


def format_pasted_text_ref(id: int, num_lines: int) -> str:
    """Format a pasted text reference."""
    if num_lines == 0:
        return f"[Pasted text #{id}]"
    return f"[Pasted text #{id} +{num_lines} lines]"


def format_image_ref(id: int) -> str:
    """Format an image reference."""
    return f"[Image #{id}]"


def parse_references(input_text: str) -> list[ParsedReference]:
    """Parse paste/image references from input text."""
    pattern = r"\[(Pasted text|Image|\.\.\.Truncated text) #(\d+)(?: \+\d+ lines)?(\.)*\]"
    matches = list(re.finditer(pattern, input_text))
    return [
        {
            "id": int(match.group(2)),
            "match": match.group(0),
            "index": match.start(),
        }
        for match in matches
        if match.group(2) and int(match.group(2)) > 0
    ]


def expand_pasted_text_refs(
    input_text: str,
    pasted_contents: dict[int, PastedContent],
) -> str:
    """
    Replace [Pasted text #N] placeholders with their actual content.

    Image refs are left alone - they become content blocks, not inlined text.
    """
    refs = parse_references(input_text)
    expanded = input_text

    # Process in reverse order to keep earlier offsets valid
    for ref in reversed(refs):
        content = pasted_contents.get(ref["id"])
        if content and content.type == "text":
            expanded = expanded[: ref["index"]] + content.content + expanded[ref["index"] + len(ref["match"]) :]

    return expanded


# Module state
_pending_entries: list[LogEntry] = []
_is_writing = False
_current_flush_promise: asyncio.Task | None = None
_cleanup_registered = False
_last_added_entry: LogEntry | None = None
_skipped_timestamps: set[float] = set()


def _get_history_path() -> str:
    """Get the path to the history file."""
    return os.path.join(get_claude_config_home_dir(), "history.jsonl")


def _deserialize_log_entry(line: str) -> LogEntry:
    """Deserialize a log entry from JSON."""
    data = json.loads(line)
    pasted_contents: dict[int, StoredPastedContent] = {}
    for id_str, stored in data.get("pastedContents", {}).items():
        pasted_contents[int(id_str)] = StoredPastedContent(
            id=stored.get("id", 0),
            type=stored.get("type", "text"),
            content=stored.get("content"),
            content_hash=stored.get("contentHash"),
            media_type=stored.get("mediaType"),
            filename=stored.get("filename"),
        )
    return LogEntry(
        display=data.get("display", ""),
        pasted_contents=pasted_contents,
        timestamp=data.get("timestamp", 0),
        project=data.get("project", ""),
        session_id=data.get("sessionId"),
    )


async def _read_lines_reverse(path: str) -> AsyncIterator[str]:
    """Read lines from a file in reverse order."""
    try:
        with open(path, encoding="utf-8") as f:
            lines = f.readlines()
        for line in reversed(lines):
            line = line.strip()
            if line:
                yield line
    except FileNotFoundError:
        return


async def _make_log_entry_reader() -> AsyncIterator[LogEntry]:
    """Create an async iterator over log entries, newest first."""
    current_session = get_session_id()

    # Start with pending entries
    for entry in reversed(_pending_entries):
        yield entry

    # Read from history file
    history_path = _get_history_path()

    async for line in _read_lines_reverse(history_path):
        try:
            entry = _deserialize_log_entry(line)
            # Skip removed entries
            if entry.session_id == current_session and entry.timestamp in _skipped_timestamps:
                continue
            yield entry
        except (json.JSONDecodeError, KeyError) as e:
            log_for_debugging(f"Failed to parse history line: {e}")


async def _resolve_stored_pasted_content(
    stored: StoredPastedContent,
) -> PastedContent | None:
    """Resolve stored paste content to full PastedContent."""
    if stored.content:
        return PastedContent(
            id=stored.id,
            type=stored.type,
            content=stored.content,
            media_type=stored.media_type,
            filename=stored.filename,
        )

    if stored.content_hash:
        # Try to retrieve from paste store
        try:
            from .utils.paste_store import retrieve_pasted_text

            content = await retrieve_pasted_text(stored.content_hash)
            if content:
                return PastedContent(
                    id=stored.id,
                    type=stored.type,
                    content=content,
                    media_type=stored.media_type,
                    filename=stored.filename,
                )
        except ImportError:
            pass

    return None


async def _log_entry_to_history_entry(entry: LogEntry) -> HistoryEntry:
    """Convert LogEntry to HistoryEntry by resolving paste references."""
    pasted_contents: dict[int, PastedContent] = {}

    for id_num, stored in entry.pasted_contents.items():
        resolved = await _resolve_stored_pasted_content(stored)
        if resolved:
            pasted_contents[id_num] = resolved

    return HistoryEntry(
        display=entry.display,
        pasted_contents=pasted_contents,
    )


async def make_history_reader() -> AsyncIterator[HistoryEntry]:
    """Create an async iterator over history entries."""
    async for entry in _make_log_entry_reader():
        yield await _log_entry_to_history_entry(entry)


async def get_timestamped_history() -> AsyncIterator[TimestampedHistoryEntry]:
    """
    Get current-project history for the ctrl+r picker.

    Deduped by display text, newest first, with timestamps.
    """
    current_project = get_project_root()
    seen: set[str] = set()

    async for entry in _make_log_entry_reader():
        if not entry or not isinstance(entry.project, str):
            continue
        if entry.project != current_project:
            continue
        if entry.display in seen:
            continue
        seen.add(entry.display)

        yield TimestampedHistoryEntry(
            display=entry.display,
            timestamp=entry.timestamp,
            _log_entry=entry,
        )

        if len(seen) >= MAX_HISTORY_ITEMS:
            return


async def get_history() -> AsyncIterator[HistoryEntry]:
    """
    Get history entries for the current project.

    Current session's entries come first, then other sessions.
    """
    current_project = get_project_root()
    current_session = get_session_id()
    other_session_entries: list[LogEntry] = []
    yielded = 0

    async for entry in _make_log_entry_reader():
        if not entry or not isinstance(entry.project, str):
            continue
        if entry.project != current_project:
            continue

        if entry.session_id == current_session:
            yield await _log_entry_to_history_entry(entry)
            yielded += 1
        else:
            other_session_entries.append(entry)

        if yielded + len(other_session_entries) >= MAX_HISTORY_ITEMS:
            break

    for entry in other_session_entries:
        if yielded >= MAX_HISTORY_ITEMS:
            return
        yield await _log_entry_to_history_entry(entry)
        yielded += 1


async def _immediate_flush_history() -> None:
    """Write pending entries to disk immediately."""
    global _pending_entries

    if not _pending_entries:
        return

    try:
        history_path = _get_history_path()

        # Ensure directory exists
        os.makedirs(os.path.dirname(history_path), exist_ok=True)

        # Write entries
        entries_to_write = _pending_entries
        _pending_entries = []

        lines = []
        for entry in entries_to_write:
            data = {
                "display": entry.display,
                "pastedContents": {
                    str(id_num): {
                        "id": stored.id,
                        "type": stored.type,
                        **({"content": stored.content} if stored.content else {}),
                        **({"contentHash": stored.content_hash} if stored.content_hash else {}),
                        **({"mediaType": stored.media_type} if stored.media_type else {}),
                        **({"filename": stored.filename} if stored.filename else {}),
                    }
                    for id_num, stored in entry.pasted_contents.items()
                },
                "timestamp": entry.timestamp,
                "project": entry.project,
                "sessionId": entry.session_id,
            }
            lines.append(json.dumps(data) + "\n")

        with open(history_path, "a", encoding="utf-8") as f:
            f.writelines(lines)

    except Exception as e:
        log_for_debugging(f"Failed to write prompt history: {e}")


async def _flush_prompt_history(retries: int = 0) -> None:
    """Flush pending history entries to disk."""
    global _is_writing

    if _is_writing or not _pending_entries:
        return

    if retries > 5:
        return

    _is_writing = True

    try:
        await _immediate_flush_history()
    finally:
        _is_writing = False

        if _pending_entries:
            await asyncio.sleep(0.5)
            await _flush_prompt_history(retries + 1)


async def _add_to_prompt_history(command: HistoryEntry | str) -> None:
    """Add a command to the prompt history."""
    global _pending_entries, _last_added_entry, _current_flush_promise

    entry = HistoryEntry(display=command) if isinstance(command, str) else command

    stored_pasted_contents: dict[int, StoredPastedContent] = {}
    for id_num, content in entry.pasted_contents.items():
        # Skip images
        if content.type == "image":
            continue

        if len(content.content) <= MAX_PASTED_CONTENT_LENGTH:
            stored_pasted_contents[id_num] = StoredPastedContent(
                id=content.id,
                type=content.type,
                content=content.content,
                media_type=content.media_type,
                filename=content.filename,
            )
        else:
            # Store large content with hash reference
            try:
                from .utils.paste_store import hash_pasted_text, store_pasted_text

                hash_value = hash_pasted_text(content.content)
                stored_pasted_contents[id_num] = StoredPastedContent(
                    id=content.id,
                    type=content.type,
                    content_hash=hash_value,
                    media_type=content.media_type,
                    filename=content.filename,
                )
                # Fire-and-forget disk write
                asyncio.create_task(store_pasted_text(hash_value, content.content))
            except ImportError:
                # Fallback to storing inline
                stored_pasted_contents[id_num] = StoredPastedContent(
                    id=content.id,
                    type=content.type,
                    content=content.content,
                    media_type=content.media_type,
                    filename=content.filename,
                )

    log_entry = LogEntry(
        display=entry.display,
        pasted_contents=stored_pasted_contents,
        timestamp=time.time() * 1000,
        project=get_project_root(),
        session_id=get_session_id(),
    )

    _pending_entries.append(log_entry)
    _last_added_entry = log_entry
    _current_flush_promise = asyncio.create_task(_flush_prompt_history())


def add_to_history(command: HistoryEntry | str) -> None:
    """Add a command to the history."""
    global _cleanup_registered

    # Skip history in verification sessions
    if is_env_truthy(os.getenv("CLAUDE_CODE_SKIP_PROMPT_HISTORY")):
        return

    # Register cleanup on first use
    if not _cleanup_registered:
        _cleanup_registered = True
        # TODO: Register cleanup handler

    asyncio.create_task(_add_to_prompt_history(command))


def clear_pending_history_entries() -> None:
    """Clear all pending history entries."""
    global _pending_entries, _last_added_entry, _skipped_timestamps
    _pending_entries = []
    _last_added_entry = None
    _skipped_timestamps.clear()


def remove_last_from_history() -> None:
    """
    Undo the most recent addToHistory call.

    Used by auto-restore-on-interrupt when Esc rewinds the conversation.
    """
    global _last_added_entry, _pending_entries

    if not _last_added_entry:
        return

    entry = _last_added_entry
    _last_added_entry = None

    if entry in _pending_entries:
        _pending_entries.remove(entry)
    else:
        _skipped_timestamps.add(entry.timestamp)
