"""
Log and transcript entry type definitions.

This module defines types for session logs, transcripts, and various
message types stored in session history.

Migrated from: types/logs.ts (331 lines)
"""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime
from typing import TYPE_CHECKING, Literal

if TYPE_CHECKING:
    pass


# ============================================================================
# Serialized Message
# ============================================================================


@dataclass
class SerializedMessage:
    """A message serialized for storage in logs."""

    cwd: str = ""
    user_type: str = ""
    session_id: str = ""
    timestamp: str = ""
    version: str = ""
    entrypoint: str | None = None  # CLAUDE_CODE_ENTRYPOINT
    git_branch: str | None = None
    slug: str | None = None  # Session slug for files like plans


# ============================================================================
# Log Option
# ============================================================================


@dataclass
class FileHistorySnapshot:
    """Snapshot of file history state."""

    pass  # Will be defined in utils/fileHistory.py


@dataclass
class ContentReplacementRecord:
    """Record of content replacement."""

    pass  # Will be defined in utils/toolResultStorage.py


@dataclass
class AttributionSnapshotData:
    """Attribution snapshot data for logs."""

    pass  # Will be defined separately


@dataclass
class ContextCollapseCommitEntry:
    """
    Persisted context-collapse commit.

    The archived messages themselves are NOT persisted — they're already
    in the transcript as ordinary user/assistant messages.
    """

    type: Literal["marble-origami-commit"] = "marble-origami-commit"
    session_id: str = ""
    collapse_id: str = ""
    summary_uuid: str = ""
    summary_content: str = ""
    summary: str = ""
    first_archived_uuid: str = ""
    last_archived_uuid: str = ""


@dataclass
class StagedCollapse:
    """Staged collapse entry."""

    start_uuid: str = ""
    end_uuid: str = ""
    summary: str = ""
    risk: float = 0.0
    staged_at: int = 0


@dataclass
class ContextCollapseSnapshotEntry:
    """
    Snapshot of the staged queue and spawn trigger state.

    Unlike commits (append-only, replay-all), snapshots are last-wins.
    """

    type: Literal["marble-origami-snapshot"] = "marble-origami-snapshot"
    session_id: str = ""
    staged: list[StagedCollapse] = field(default_factory=list)
    armed: bool = False
    last_spawn_tokens: int = 0


@dataclass
class PersistedWorktreeSession:
    """
    Worktree session state persisted to the transcript for resume.

    Subset of WorktreeSession — excludes ephemeral fields that are only
    used for first-run analytics.
    """

    original_cwd: str = ""
    worktree_path: str = ""
    worktree_name: str = ""
    session_id: str = ""
    worktree_branch: str | None = None
    original_branch: str | None = None
    original_head_commit: str | None = None
    tmux_session_name: str | None = None
    hook_based: bool = False


@dataclass
class LogOption:
    """Represents a log/session option for display and selection."""

    date: str
    messages: list[SerializedMessage]
    value: int
    created: datetime
    modified: datetime
    first_prompt: str
    message_count: int
    is_sidechain: bool
    full_path: str | None = None
    file_size: int | None = None
    is_lite: bool = False
    session_id: str | None = None
    team_name: str | None = None
    agent_name: str | None = None
    agent_color: str | None = None
    agent_setting: str | None = None
    is_teammate: bool = False
    leaf_uuid: str | None = None
    summary: str | None = None
    custom_title: str | None = None
    tag: str | None = None
    file_history_snapshots: list[FileHistorySnapshot] | None = None
    attribution_snapshots: list[AttributionSnapshotData] | None = None
    context_collapse_commits: list[ContextCollapseCommitEntry] | None = None
    context_collapse_snapshot: ContextCollapseSnapshotEntry | None = None
    git_branch: str | None = None
    project_path: str | None = None
    pr_number: int | None = None
    pr_url: str | None = None
    pr_repository: str | None = None
    mode: Literal["coordinator", "normal"] | None = None
    worktree_session: PersistedWorktreeSession | None = None
    content_replacements: list[ContentReplacementRecord] | None = None


def sort_logs(logs: list[LogOption]) -> list[LogOption]:
    """
    Sort logs by modified date (newest first).

    If modified dates are equal, sort by created date (newest first).
    """
    return sorted(
        logs,
        key=lambda log: (log.modified, log.created),
        reverse=True,
    )


# ============================================================================
# Transcript Message Types
# ============================================================================


@dataclass
class SummaryMessage:
    """Summary message for a session."""

    type: Literal["summary"] = "summary"
    leaf_uuid: str = ""
    summary: str = ""


@dataclass
class CustomTitleMessage:
    """User-set custom title for a session."""

    type: Literal["custom-title"] = "custom-title"
    session_id: str = ""
    custom_title: str = ""


@dataclass
class AiTitleMessage:
    """AI-generated session title."""

    type: Literal["ai-title"] = "ai-title"
    session_id: str = ""
    ai_title: str = ""


@dataclass
class LastPromptMessage:
    """Last prompt message for quick access."""

    type: Literal["last-prompt"] = "last-prompt"
    session_id: str = ""
    last_prompt: str = ""


@dataclass
class TaskSummaryMessage:
    """
    Periodic fork-generated summary of what the agent is currently doing.

    Written every min(5 steps, 2min) so `claude ps` can show something
    more useful than the last user prompt.
    """

    type: Literal["task-summary"] = "task-summary"
    session_id: str = ""
    summary: str = ""
    timestamp: str = ""


@dataclass
class TagMessage:
    """Tag message for session categorization."""

    type: Literal["tag"] = "tag"
    session_id: str = ""
    tag: str = ""


@dataclass
class AgentNameMessage:
    """Agent's custom name."""

    type: Literal["agent-name"] = "agent-name"
    session_id: str = ""
    agent_name: str = ""


@dataclass
class AgentColorMessage:
    """Agent's color for display."""

    type: Literal["agent-color"] = "agent-color"
    session_id: str = ""
    agent_color: str = ""


@dataclass
class AgentSettingMessage:
    """Agent definition used."""

    type: Literal["agent-setting"] = "agent-setting"
    session_id: str = ""
    agent_setting: str = ""


@dataclass
class PRLinkMessage:
    """
    PR link message stored in session transcript.

    Links a session to a GitHub pull request for tracking and navigation.
    """

    type: Literal["pr-link"] = "pr-link"
    session_id: str = ""
    pr_number: int = 0
    pr_url: str = ""
    pr_repository: str = ""
    timestamp: str = ""


@dataclass
class ModeEntry:
    """Session mode for coordinator/normal detection."""

    type: Literal["mode"] = "mode"
    session_id: str = ""
    mode: Literal["coordinator", "normal"] = "normal"


@dataclass
class WorktreeStateEntry:
    """
    Records whether the session is currently inside a worktree.

    Last-wins: an enter writes the session, an exit writes None.
    """

    type: Literal["worktree-state"] = "worktree-state"
    session_id: str = ""
    worktree_session: PersistedWorktreeSession | None = None


@dataclass
class ContentReplacementEntry:
    """
    Records content blocks whose in-context representation was replaced.

    Replayed on resume for prompt cache stability.
    """

    type: Literal["content-replacement"] = "content-replacement"
    session_id: str = ""
    agent_id: str | None = None  # AgentId
    replacements: list[ContentReplacementRecord] = field(default_factory=list)


@dataclass
class FileHistorySnapshotMessage:
    """File history snapshot message."""

    type: Literal["file-history-snapshot"] = "file-history-snapshot"
    message_id: str = ""
    snapshot: FileHistorySnapshot | None = None
    is_snapshot_update: bool = False


@dataclass
class FileAttributionState:
    """Per-file attribution state tracking Claude's character contributions."""

    content_hash: str = ""  # SHA-256 hash of file content
    claude_contribution: int = 0  # Characters written by Claude
    mtime: int = 0  # File modification time


@dataclass
class AttributionSnapshotMessage:
    """
    Attribution snapshot message stored in session transcript.

    Tracks character-level contributions by Claude for commit attribution.
    """

    type: Literal["attribution-snapshot"] = "attribution-snapshot"
    message_id: str = ""
    surface: str = ""  # Client surface (cli, ide, web, api)
    file_states: dict[str, FileAttributionState] = field(default_factory=dict)
    prompt_count: int | None = None
    prompt_count_at_last_commit: int | None = None
    permission_prompt_count: int | None = None
    permission_prompt_count_at_last_commit: int | None = None
    escape_count: int | None = None
    escape_count_at_last_commit: int | None = None


@dataclass
class TranscriptMessage(SerializedMessage):
    """A message in the transcript with tree structure."""

    parent_uuid: str | None = None
    logical_parent_uuid: str | None = None
    is_sidechain: bool = False
    git_branch: str | None = None
    agent_id: str | None = None
    team_name: str | None = None
    agent_name: str | None = None
    agent_color: str | None = None
    prompt_id: str | None = None


@dataclass
class SpeculationAcceptMessage:
    """Message recording acceptance of speculative execution."""

    type: Literal["speculation-accept"] = "speculation-accept"
    timestamp: str = ""
    time_saved_ms: int = 0


# Union type for all entry types
Entry = (
    TranscriptMessage
    | SummaryMessage
    | CustomTitleMessage
    | AiTitleMessage
    | LastPromptMessage
    | TaskSummaryMessage
    | TagMessage
    | AgentNameMessage
    | AgentColorMessage
    | AgentSettingMessage
    | PRLinkMessage
    | ModeEntry
    | WorktreeStateEntry
    | ContentReplacementEntry
    | FileHistorySnapshotMessage
    | AttributionSnapshotMessage
    | SpeculationAcceptMessage
    | ContextCollapseCommitEntry
    | ContextCollapseSnapshotEntry
)
