"""
Configuration type definitions.

Migrated from: utils/config.ts (partial - 1818 lines)
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Literal


@dataclass
class ImageDimensions:
    """Image dimension info for coordinate mapping."""

    width: int
    height: int
    original_width: int | None = None
    original_height: int | None = None


@dataclass
class PastedContent:
    """Content pasted into the prompt."""

    id: int  # Sequential numeric ID
    type: Literal["text", "image"]
    content: str
    media_type: str | None = None  # e.g., 'image/png', 'image/jpeg'
    filename: str | None = None  # Display name for images
    dimensions: ImageDimensions | None = None
    source_path: str | None = None  # Original file path for images


@dataclass
class HistoryEntry:
    """A history entry."""

    display: str
    pasted_contents: dict[int, PastedContent] = field(default_factory=dict)


ReleaseChannel = Literal["stable", "latest"]


@dataclass
class WorktreeSession:
    """Active worktree session info."""

    original_cwd: str
    worktree_path: str
    worktree_name: str
    session_id: str
    original_branch: str | None = None
    hook_based: bool = False


@dataclass
class ProjectConfig:
    """Per-project configuration."""

    allowed_tools: list[str] = field(default_factory=list)
    mcp_context_uris: list[str] = field(default_factory=list)
    mcp_servers: dict[str, Any] | None = None

    # Session metrics
    last_api_duration: int | None = None
    last_api_duration_without_retries: int | None = None
    last_tool_duration: int | None = None
    last_cost: float | None = None
    last_duration: int | None = None
    last_lines_added: int | None = None
    last_lines_removed: int | None = None
    last_session_id: str | None = None
    last_model_usage: dict[str, dict[str, Any]] | None = None

    # Example files
    example_files: list[str] | None = None
    example_files_generated_at: int | None = None

    # Trust and onboarding
    has_trust_dialog_accepted: bool = False
    has_completed_project_onboarding: bool = False
    project_onboarding_seen_count: int = 0
    has_claude_md_external_includes_approved: bool = False
    has_claude_md_external_includes_warning_shown: bool = False

    # MCP server settings
    enabled_mcpjson_servers: list[str] = field(default_factory=list)
    disabled_mcpjson_servers: list[str] = field(default_factory=list)
    enable_all_project_mcp_servers: bool = False
    disabled_mcp_servers: list[str] = field(default_factory=list)
    enabled_mcp_servers: list[str] = field(default_factory=list)

    # Worktree session
    active_worktree_session: WorktreeSession | None = None
    remote_control_spawn_mode: Literal["same-dir", "worktree"] | None = None


BillingType = Literal[
    "aws_marketplace",
    "gcp_marketplace",
    "google_play",
    "web",
    "apple_iap",
]


@dataclass
class AccountInfo:
    """OAuth account information."""

    account_uuid: str
    email_address: str
    organization_uuid: str | None = None
    organization_name: str | None = None
    organization_role: str | None = None
    workspace_role: str | None = None
    display_name: str | None = None
    has_extra_usage_enabled: bool = False
    billing_type: BillingType | None = None
    account_created_at: str | None = None
    subscription_created_at: str | None = None


InstallMethod = Literal["local", "native", "global", "unknown"]

ThemeSetting = Literal["dark", "light", "light-daltonism", "system"]

NotificationChannel = Literal[
    "auto",
    "iterm2",
    "iterm2_with_bell",
    "kitty",
    "ghostty",
    "terminal_bell",
    "notifications_disabled",
]

EditorMode = Literal["emacs", "vim", "default"]

DiffTool = Literal["terminal", "auto"]


@dataclass
class GlobalConfig:
    """Global configuration."""

    # API settings
    api_key_helper: str | None = None

    # Projects
    projects: dict[str, ProjectConfig] = field(default_factory=dict)

    # General settings
    num_startups: int = 0
    install_method: InstallMethod = "unknown"
    auto_updates: bool = True
    auto_updates_protected_for_native: bool = False

    # User settings
    user_id: str | None = None
    theme: ThemeSetting = "dark"
    has_completed_onboarding: bool = False
    last_onboarding_version: str | None = None

    # OAuth
    oauth_account: AccountInfo | None = None

    # Preferences
    editor_mode: EditorMode = "default"
    preferred_notif_channel: NotificationChannel = "auto"
    verbose_mode: bool = False

    # Release channel
    release_channel: ReleaseChannel = "stable"

    # MCP settings
    mcp_servers: dict[str, Any] = field(default_factory=dict)

    # History
    history: list[HistoryEntry] = field(default_factory=list)

    # Client data cache (GrowthBook features etc.)
    client_data_cache: dict[str, str] | None = None

    # Telemetry
    has_acked_telemetry: bool = False
