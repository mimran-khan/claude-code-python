"""Tool base classes and types for Claude Code."""

from abc import ABC, abstractmethod
from collections.abc import Callable, Iterable
from dataclasses import dataclass, field
from typing import (
    Any,
    Generic,
    Literal,
    TypeVar,
)

# Type definitions
ToolInputJSONSchema = dict[str, Any]


@dataclass
class QueryChainTracking:
    """Tracking information for query chains."""

    chain_id: str
    depth: int


@dataclass
class ValidationResult:
    """Result of input validation."""

    result: bool
    message: str = ""
    error_code: int = 0


PermissionMode = Literal["default", "plan", "bypassPermissions", "auto"]


@dataclass
class AdditionalWorkingDirectory:
    """Additional working directory configuration."""

    path: str
    read_only: bool = False


@dataclass(frozen=True)
class ToolPermissionContext:
    """Permission context for tool execution."""

    mode: PermissionMode = "default"
    additional_working_directories: dict[str, AdditionalWorkingDirectory] = field(default_factory=dict)
    always_allow_rules: dict[str, Any] = field(default_factory=dict)
    always_deny_rules: dict[str, Any] = field(default_factory=dict)
    always_ask_rules: dict[str, Any] = field(default_factory=dict)
    is_bypass_permissions_mode_available: bool = False
    is_auto_mode_available: bool = False
    stripped_dangerous_rules: dict[str, Any] | None = None
    should_avoid_permission_prompts: bool = False
    await_automated_checks_before_dialog: bool = False
    pre_plan_mode: PermissionMode | None = None


def get_empty_tool_permission_context() -> ToolPermissionContext:
    """Get an empty tool permission context."""
    return ToolPermissionContext()


@dataclass
class CompactProgressEvent:
    """Event for compact progress tracking."""

    type: Literal["hooks_start", "compact_start", "compact_end"]
    hook_type: Literal["pre_compact", "post_compact", "session_start"] | None = None


@dataclass
class FileStateCache:
    """Cache for file state."""

    cache: dict[str, Any] = field(default_factory=dict)


@dataclass
class FileHistoryState:
    """State for file history tracking."""

    snapshots: list[dict[str, Any]] = field(default_factory=list)


@dataclass
class AttributionState:
    """State for commit attribution."""

    attributions: dict[str, Any] = field(default_factory=dict)


@dataclass
class AppState:
    """Application state."""

    tool_permission_context: ToolPermissionContext = field(default_factory=get_empty_tool_permission_context)


@dataclass
class ToolUseContext:
    """Context for tool execution."""

    options: dict[str, Any] = field(default_factory=dict)
    abort_controller: Any | None = None
    read_file_state: FileStateCache = field(default_factory=FileStateCache)
    messages: list[Any] = field(default_factory=list)

    # Callbacks
    get_app_state: Callable[[], AppState] | None = None
    set_app_state: Callable[[Callable[[AppState], AppState]], None] | None = None
    set_in_progress_tool_use_ids: Callable[[Callable[[set[str]], set[str]]], None] | None = None
    set_response_length: Callable[[Callable[[int], int]], None] | None = None
    update_file_history_state: Callable[[Callable[[FileHistoryState], FileHistoryState]], None] | None = None
    update_attribution_state: Callable[[Callable[[AttributionState], AttributionState]], None] | None = None

    # Optional context
    agent_id: str | None = None
    agent_type: str | None = None
    tool_use_id: str | None = None
    query_tracking: QueryChainTracking | None = None
    file_reading_limits: dict[str, int] | None = None
    glob_limits: dict[str, int] | None = None


# Progress types
@dataclass
class BashProgress:
    """Progress for bash tool execution."""

    type: Literal["bash"] = "bash"
    output: str = ""
    exit_code: int | None = None


@dataclass
class WebSearchProgress:
    """Progress for web search."""

    type: Literal["web_search"] = "web_search"
    status: str = ""


@dataclass
class AgentToolProgress:
    """Progress for agent tool."""

    type: Literal["agent"] = "agent"
    status: str = ""


@dataclass
class MCPProgress:
    """Progress for MCP operations."""

    type: Literal["mcp"] = "mcp"
    status: str = ""


@dataclass
class REPLToolProgress:
    """Progress for REPL tool."""

    type: Literal["repl"] = "repl"
    output: str = ""


@dataclass
class SkillToolProgress:
    """Progress for skill tool."""

    type: Literal["skill"] = "skill"
    status: str = ""


@dataclass
class TaskOutputProgress:
    """Progress for task output."""

    type: Literal["task_output"] = "task_output"
    content: str = ""


ToolProgressData = (
    BashProgress
    | WebSearchProgress
    | AgentToolProgress
    | MCPProgress
    | REPLToolProgress
    | SkillToolProgress
    | TaskOutputProgress
)


@dataclass
class HookProgress:
    """Progress for hook execution."""

    type: Literal["hook_progress"] = "hook_progress"
    hook_name: str = ""
    status: str = ""


Progress = ToolProgressData | HookProgress

ProgressPayloadT = TypeVar("ProgressPayloadT", bound=Progress)


@dataclass
class ProgressMessage(Generic[ProgressPayloadT]):
    """Progress message wrapper."""

    data: ProgressPayloadT


def filter_tool_progress_messages(
    progress_messages: Iterable[ProgressMessage[Progress]],
) -> list[ProgressMessage[ToolProgressData]]:
    """Filter progress messages to only tool progress."""
    return [
        msg for msg in progress_messages if hasattr(msg, "data") and getattr(msg.data, "type", None) != "hook_progress"
    ]


T = TypeVar("T")


@dataclass
class ToolProgress(Generic[T]):
    """Tool progress with ID."""

    tool_use_id: str
    data: T


@dataclass
class ToolResult(Generic[T]):
    """Result of a tool execution."""

    data: T
    new_messages: list[Any] | None = None
    context_modifier: Callable[[ToolUseContext], ToolUseContext] | None = None
    mcp_meta: dict[str, Any] | None = None


ToolCallProgress = Callable[[ToolProgress[ToolProgressData]], None]


def tool_matches_name(
    tool: dict[str, Any],
    name: str,
) -> bool:
    """Check if a tool matches the given name (primary name or alias)."""
    if tool.get("name") == name:
        return True
    aliases = tool.get("aliases", [])
    return name in aliases


class Tool(ABC):
    """Abstract base class for tools."""

    name: str
    description: str
    input_schema: ToolInputJSONSchema
    aliases: list[str] = []

    # Tool characteristics
    is_read_only: bool = False
    is_concurrency_safe: bool = True
    user_facing_name: str | None = None

    @abstractmethod
    async def call(
        self,
        input_data: dict[str, Any],
        context: ToolUseContext,
        progress_callback: ToolCallProgress | None = None,
    ) -> ToolResult[Any]:
        """Execute the tool with given input."""
        pass

    def validate_input(self, input_data: dict[str, Any]) -> ValidationResult:
        """Validate the input data."""
        return ValidationResult(result=True)

    def get_tool_use_summary(self, input_data: dict[str, Any]) -> str:
        """Get a summary of the tool use for display."""
        return f"{self.name}(...)"

    def is_enabled(self) -> bool:
        """Whether this tool is available in the current environment (subclasses may override)."""
        return True


# Type alias for a collection of tools
Tools = list[Tool]
