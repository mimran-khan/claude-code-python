"""
Application state types and initialization.

Migrated from: state/AppStateStore.ts
"""

from collections.abc import Callable
from dataclasses import dataclass, field
from typing import Any, Literal

ViewSelectionMode = Literal["none", "viewing-agent"]


@dataclass
class CompletionBoundary:
    """Boundary marker for completion."""

    type: Literal["complete", "bash", "edit", "denied_tool"]
    completed_at: float
    output_tokens: int | None = None
    command: str | None = None
    tool_name: str | None = None
    file_path: str | None = None
    detail: str | None = None


@dataclass
class SpeculationResult:
    """Result of speculative execution."""

    messages: list[Any]  # Message[]
    boundary: CompletionBoundary | None
    time_saved_ms: float


@dataclass
class IdleSpeculationState:
    """Idle speculation state."""

    status: Literal["idle"] = "idle"


@dataclass
class ActiveSpeculationState:
    """Active speculation state."""

    status: Literal["active"] = "active"
    id: str = ""
    abort: Callable[[], None] = lambda: None
    start_time: float = 0.0
    messages_ref: dict[str, list[Any]] = field(default_factory=lambda: {"current": []})
    written_paths_ref: dict[str, set[str]] = field(default_factory=lambda: {"current": set()})
    boundary: CompletionBoundary | None = None
    suggestion_length: int = 0
    tool_use_count: int = 0
    is_pipelined: bool = False
    context_ref: dict[str, Any] = field(default_factory=dict)
    pipelined_suggestion: dict[str, Any] | None = None


SpeculationState = IdleSpeculationState | ActiveSpeculationState
IDLE_SPECULATION_STATE = IdleSpeculationState()


@dataclass
class SettingsState:
    """User settings state."""

    verbose: int = 0
    thinking: bool = False
    permission_mode: str = "default"
    model_setting: str | None = None


@dataclass
class MCPState:
    """MCP connection state."""

    servers: dict[str, Any] = field(default_factory=dict)
    resources: list[Any] = field(default_factory=list)


@dataclass
class AppState:
    """Main application state.

    Tracks all runtime state for the Claude Code session.
    """

    # Core state
    messages: list[Any] = field(default_factory=list)
    current_agent_id: str | None = None
    viewing_agent_task_id: str | None = None
    view_selection_mode: ViewSelectionMode = "none"
    is_ultraplan_mode: bool = False
    ultraplan_session_url: str | None = None
    ultraplan_launching: bool = False
    main_loop_model: str | None = None

    # UI state
    is_loading: bool = False
    is_paused: bool = False
    has_completed: bool = False

    # Speculation
    speculation: SpeculationState = field(default_factory=lambda: IDLE_SPECULATION_STATE)

    # Settings
    settings: SettingsState = field(default_factory=SettingsState)

    # Tool permissions
    tool_permission_context: dict[str, Any] = field(default_factory=dict)

    # MCP
    mcp: MCPState = field(default_factory=MCPState)

    # Tasks
    tasks: dict[str, Any] = field(default_factory=dict)

    # Plugins
    loaded_plugins: list[Any] = field(default_factory=list)
    plugin_errors: list[Any] = field(default_factory=list)

    # Notifications
    notifications: list[Any] = field(default_factory=list)

    # Todo
    todo_list: Any | None = None

    # Attribution
    attribution_state: dict[str, Any] = field(default_factory=dict)

    # Agents
    agent_definitions: Any | None = None
    agent_colors: dict[str, str] = field(default_factory=dict)

    # Session hooks
    session_hooks_state: dict[str, Any] = field(default_factory=dict)

    # File history
    file_history_state: Any | None = None


def create_initial_app_state() -> AppState:
    """Create initial application state."""
    return AppState(
        tool_permission_context={},
        settings=SettingsState(
            thinking=False,  # Would check shouldEnableThinkingByDefault()
        ),
    )
