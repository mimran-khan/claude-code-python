"""
Session Storage.

Handles reading and writing session data to disk.
"""

from __future__ import annotations

import json
import os
import time
from dataclasses import dataclass, field
from pathlib import Path
from typing import TYPE_CHECKING

from .types import PersistedSession, SerializedMessage, TranscriptEntry

if TYPE_CHECKING:
    pass

# Try to import aiofiles, fall back to sync file ops
try:
    import aiofiles

    HAS_AIOFILES = True
except ImportError:
    HAS_AIOFILES = False


def get_claude_config_home() -> Path:
    """Get the Claude config home directory.

    Uses CLAUDE_CONFIG_DIR if set, otherwise defaults to ~/.claude.
    """
    config_dir = os.environ.get("CLAUDE_CONFIG_DIR")
    if config_dir:
        return Path(config_dir)
    return Path.home() / ".claude"


def get_sessions_root() -> Path:
    """Get the root directory for session storage.

    Returns:
        Path to the sessions directory
    """
    return get_claude_config_home() / "projects"


def get_session_dir(session_id: str, project_dir: str | None = None) -> Path:
    """Get the directory for a specific session.

    Args:
        session_id: The session ID
        project_dir: Optional project directory (for project-specific sessions)

    Returns:
        Path to the session directory
    """
    if project_dir:
        # Hash the project directory for the path
        import hashlib

        project_hash = hashlib.sha256(project_dir.encode()).hexdigest()[:16]
        return get_sessions_root() / project_hash / session_id

    return get_sessions_root() / "default" / session_id


@dataclass
class SessionStorage:
    """Storage handler for session data."""

    session_id: str = ""
    project_dir: str = ""
    _dir: Path | None = field(default=None, repr=False)
    _initialized: bool = field(default=False, repr=False)

    @property
    def session_dir(self) -> Path:
        """Get the session directory."""
        if self._dir is None:
            self._dir = get_session_dir(self.session_id, self.project_dir or None)
        return self._dir

    @property
    def transcript_path(self) -> Path:
        """Get the path to the transcript file."""
        return self.session_dir / "transcript.jsonl"

    @property
    def metadata_path(self) -> Path:
        """Get the path to the metadata file."""
        return self.session_dir / "session.json"

    async def initialize(self) -> None:
        """Initialize the session storage directory.

        Note: Requires aiofiles package to be installed for async file operations.
        """
        if self._initialized:
            return

        self.session_dir.mkdir(parents=True, exist_ok=True)
        self._initialized = True

    async def save_message(self, message: SerializedMessage) -> None:
        """Save a message to the transcript.

        Args:
            message: The message to save
        """
        await self.initialize()

        entry = TranscriptEntry(
            type="message",
            message=message,
            timestamp=time.time(),
        )

        line = json.dumps(entry.to_dict()) + "\n"

        if HAS_AIOFILES:
            async with aiofiles.open(self.transcript_path, "a") as f:
                await f.write(line)
        else:
            with open(self.transcript_path, "a") as f:
                f.write(line)

    async def save_entry(self, entry: TranscriptEntry) -> None:
        """Save a transcript entry.

        Args:
            entry: The entry to save
        """
        await self.initialize()

        line = json.dumps(entry.to_dict()) + "\n"

        if HAS_AIOFILES:
            async with aiofiles.open(self.transcript_path, "a") as f:
                await f.write(line)
        else:
            with open(self.transcript_path, "a") as f:
                f.write(line)

    async def load_messages(self) -> list[SerializedMessage]:
        """Load all messages from the transcript.

        Returns:
            List of serialized messages
        """
        if not self.transcript_path.exists():
            return []

        messages: list[SerializedMessage] = []

        if HAS_AIOFILES:
            async with aiofiles.open(self.transcript_path) as f:
                async for line in f:
                    line = line.strip()
                    if not line:
                        continue
                    try:
                        data = json.loads(line)
                        entry = TranscriptEntry.from_dict(data)
                        if entry.message:
                            messages.append(entry.message)
                    except json.JSONDecodeError:
                        continue
        else:
            with open(self.transcript_path) as f:
                for line in f:
                    line = line.strip()
                    if not line:
                        continue
                    try:
                        data = json.loads(line)
                        entry = TranscriptEntry.from_dict(data)
                        if entry.message:
                            messages.append(entry.message)
                    except json.JSONDecodeError:
                        continue

        return messages

    async def load_entries(self) -> list[TranscriptEntry]:
        """Load all transcript entries.

        Returns:
            List of transcript entries
        """
        if not self.transcript_path.exists():
            return []

        entries: list[TranscriptEntry] = []

        if HAS_AIOFILES:
            async with aiofiles.open(self.transcript_path) as f:
                async for line in f:
                    line = line.strip()
                    if not line:
                        continue
                    try:
                        data = json.loads(line)
                        entries.append(TranscriptEntry.from_dict(data))
                    except json.JSONDecodeError:
                        continue
        else:
            with open(self.transcript_path) as f:
                for line in f:
                    line = line.strip()
                    if not line:
                        continue
                    try:
                        data = json.loads(line)
                        entries.append(TranscriptEntry.from_dict(data))
                    except json.JSONDecodeError:
                        continue

        return entries

    async def save_metadata(self, session: PersistedSession) -> None:
        """Save session metadata.

        Args:
            session: The session metadata to save
        """
        await self.initialize()

        if HAS_AIOFILES:
            async with aiofiles.open(self.metadata_path, "w") as f:
                await f.write(json.dumps(session.to_dict(), indent=2))
        else:
            with open(self.metadata_path, "w") as f:
                f.write(json.dumps(session.to_dict(), indent=2))

    async def load_metadata(self) -> PersistedSession | None:
        """Load session metadata.

        Returns:
            The session metadata, or None if not found
        """
        if not self.metadata_path.exists():
            return None

        try:
            if HAS_AIOFILES:
                async with aiofiles.open(self.metadata_path) as f:
                    content = await f.read()
                    data = json.loads(content)
                    return PersistedSession.from_dict(data)
            else:
                with open(self.metadata_path) as f:
                    content = f.read()
                    data = json.loads(content)
                    return PersistedSession.from_dict(data)
        except (json.JSONDecodeError, OSError):
            return None

    async def clear(self) -> None:
        """Clear all session data."""
        if self.transcript_path.exists():
            self.transcript_path.unlink()
        if self.metadata_path.exists():
            self.metadata_path.unlink()

    def exists(self) -> bool:
        """Check if session data exists."""
        return self.session_dir.exists() and (self.transcript_path.exists() or self.metadata_path.exists())


async def save_message(
    session_id: str,
    message: SerializedMessage,
    *,
    project_dir: str = "",
) -> None:
    """Save a message to session storage.

    Args:
        session_id: The session ID
        message: The message to save
        project_dir: Optional project directory
    """
    storage = SessionStorage(session_id=session_id, project_dir=project_dir)
    await storage.save_message(message)


async def load_messages(
    session_id: str,
    *,
    project_dir: str = "",
) -> list[SerializedMessage]:
    """Load messages from session storage.

    Args:
        session_id: The session ID
        project_dir: Optional project directory

    Returns:
        List of serialized messages
    """
    storage = SessionStorage(session_id=session_id, project_dir=project_dir)
    return await storage.load_messages()


async def list_sessions(
    project_dir: str | None = None,
) -> list[PersistedSession]:
    """List all sessions.

    Args:
        project_dir: Optional project directory to filter by

    Returns:
        List of persisted sessions
    """
    sessions: list[PersistedSession] = []

    root = get_sessions_root()
    if not root.exists():
        return sessions

    for project_path in root.iterdir():
        if not project_path.is_dir():
            continue

        for session_path in project_path.iterdir():
            if not session_path.is_dir():
                continue

            metadata_path = session_path / "session.json"
            if not metadata_path.exists():
                continue

            try:
                if HAS_AIOFILES:
                    async with aiofiles.open(metadata_path) as f:
                        content = await f.read()
                else:
                    with open(metadata_path) as f:
                        content = f.read()

                data = json.loads(content)
                session = PersistedSession.from_dict(data)

                # Filter by project directory if specified
                if project_dir and session.project_dir != project_dir:
                    continue

                sessions.append(session)
            except (json.JSONDecodeError, OSError):
                continue

    # Sort by updated_at descending
    sessions.sort(key=lambda s: s.updated_at, reverse=True)

    return sessions
