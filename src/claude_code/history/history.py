"""
History Implementation.

Manages command and prompt history.
"""

from __future__ import annotations

import json
import os
import re
from dataclasses import dataclass, field
from pathlib import Path
from typing import Literal

MAX_HISTORY_ITEMS = 100
MAX_PASTED_CONTENT_LENGTH = 1024


@dataclass
class PastedContent:
    """Pasted content entry."""

    id: int
    type: Literal["text", "image"]
    content: str | None = None
    content_hash: str | None = None
    media_type: str | None = None
    filename: str | None = None


@dataclass
class HistoryEntry:
    """A single history entry."""

    prompt: str
    pasted_content: list[PastedContent] = field(default_factory=list)
    timestamp: str | None = None
    session_id: str | None = None
    project_root: str | None = None


def get_pasted_text_ref_num_lines(text: str) -> int:
    """Get the number of lines in pasted text for reference formatting.

    Note: We count newlines, not lines. "line1\\nline2\\nline3" has 2 newlines.

    Args:
        text: The pasted text

    Returns:
        The number of newlines in the text
    """
    return len(re.findall(r"\r\n|\r|\n", text))


def format_pasted_text_ref(id: int, num_lines: int) -> str:
    """Format a pasted text reference.

    Args:
        id: The paste ID
        num_lines: The number of extra lines

    Returns:
        The formatted reference string
    """
    if num_lines == 0:
        return f"[Pasted text #{id}]"
    return f"[Pasted text #{id} +{num_lines} lines]"


def format_image_ref(id: int) -> str:
    """Format an image reference.

    Args:
        id: The image ID

    Returns:
        The formatted reference string
    """
    return f"[Image #{id}]"


@dataclass
class ParsedReference:
    """A parsed reference from input."""

    id: int
    match: str
    index: int


def parse_references(input_text: str) -> list[ParsedReference]:
    """Parse references from input text.

    Args:
        input_text: The input text to parse

    Returns:
        List of parsed references
    """
    pattern = r"\[(Pasted text|Image|\.\.\.Truncated text) #(\d+)(?: \+\d+ lines)?(\.)*\]"
    matches = []

    for m in re.finditer(pattern, input_text):
        ref_id = int(m.group(2) or "0")
        if ref_id > 0:
            matches.append(
                ParsedReference(
                    id=ref_id,
                    match=m.group(0),
                    index=m.start(),
                )
            )

    return matches


class History:
    """Manages command and prompt history."""

    def __init__(self, history_path: str | None = None):
        """Initialize history.

        Args:
            history_path: Path to the history file
        """
        self._history_path = history_path
        self._entries: list[HistoryEntry] = []
        self._loaded = False

    @property
    def history_path(self) -> str:
        """Get the history file path."""
        if self._history_path:
            return self._history_path

        from ..utils.env import get_claude_config_home_dir

        return os.path.join(get_claude_config_home_dir(), "history.jsonl")

    def load(self) -> None:
        """Load history from disk."""
        if self._loaded:
            return

        path = Path(self.history_path)
        if not path.exists():
            self._loaded = True
            return

        try:
            with open(path, encoding="utf-8") as f:
                for line in f:
                    line = line.strip()
                    if not line:
                        continue
                    try:
                        data = json.loads(line)
                        entry = HistoryEntry(
                            prompt=data.get("prompt", ""),
                            pasted_content=[
                                PastedContent(
                                    id=pc.get("id", 0),
                                    type=pc.get("type", "text"),
                                    content=pc.get("content"),
                                    content_hash=pc.get("contentHash"),
                                    media_type=pc.get("mediaType"),
                                    filename=pc.get("filename"),
                                )
                                for pc in data.get("pastedContent", [])
                            ],
                            timestamp=data.get("timestamp"),
                            session_id=data.get("sessionId"),
                            project_root=data.get("projectRoot"),
                        )
                        self._entries.append(entry)
                    except json.JSONDecodeError:
                        continue
        except Exception:
            pass

        self._loaded = True

    def add(self, entry: HistoryEntry) -> None:
        """Add an entry to history.

        Args:
            entry: The entry to add
        """
        self.load()
        self._entries.append(entry)

        # Trim to max items
        if len(self._entries) > MAX_HISTORY_ITEMS:
            self._entries = self._entries[-MAX_HISTORY_ITEMS:]

        # Save to disk
        self._save_entry(entry)

    def _save_entry(self, entry: HistoryEntry) -> None:
        """Save a single entry to disk.

        Args:
            entry: The entry to save
        """
        path = Path(self.history_path)
        path.parent.mkdir(parents=True, exist_ok=True)

        data = {
            "prompt": entry.prompt,
            "pastedContent": [
                {
                    "id": pc.id,
                    "type": pc.type,
                    "content": pc.content,
                    "contentHash": pc.content_hash,
                    "mediaType": pc.media_type,
                    "filename": pc.filename,
                }
                for pc in entry.pasted_content
            ],
            "timestamp": entry.timestamp,
            "sessionId": entry.session_id,
            "projectRoot": entry.project_root,
        }

        with open(path, "a", encoding="utf-8") as f:
            f.write(json.dumps(data) + "\n")

    def get_recent(self, count: int = 10) -> list[HistoryEntry]:
        """Get recent history entries.

        Args:
            count: The number of entries to return

        Returns:
            List of recent entries
        """
        self.load()
        return self._entries[-count:]

    def search(self, query: str) -> list[HistoryEntry]:
        """Search history for matching entries.

        Args:
            query: The search query

        Returns:
            List of matching entries
        """
        self.load()
        query_lower = query.lower()
        return [entry for entry in self._entries if query_lower in entry.prompt.lower()]
