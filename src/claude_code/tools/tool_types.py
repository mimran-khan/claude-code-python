"""
Extended Tool Types.

Additional type definitions for the tool system extracted from Tool.ts.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import (
    TYPE_CHECKING,
    Any,
    Generic,
    Literal,
    TypeVar,
)

if TYPE_CHECKING:
    pass


# ============================================================================
# Query Chain Tracking
# ============================================================================


@dataclass
class QueryChainTracking:
    """Track query chains for nested agent calls."""

    chain_id: str = ""
    depth: int = 0


# ============================================================================
# Validation Result
# ============================================================================


@dataclass
class ValidationResultSuccess:
    """Successful validation result."""

    result: Literal[True] = True


@dataclass
class ValidationResultFailure:
    """Failed validation result."""

    result: Literal[False] = False
    message: str = ""
    error_code: int = 0


ValidationResult = ValidationResultSuccess | ValidationResultFailure


def validation_success() -> ValidationResult:
    """Create a successful validation result."""
    return ValidationResultSuccess()


def validation_failure(message: str, error_code: int = 0) -> ValidationResult:
    """Create a failed validation result."""
    return ValidationResultFailure(result=False, message=message, error_code=error_code)


# ============================================================================
# Tool Permission Context
# ============================================================================


@dataclass
class AdditionalWorkingDirectory:
    """An additional working directory with permissions."""

    path: str
    source: str = ""


@dataclass
class ToolPermissionContext:
    """Context for tool permission checking."""

    mode: str = "default"
    additional_working_directories: dict[str, AdditionalWorkingDirectory] = field(default_factory=dict)
    always_allow_rules: dict[str, list[str]] = field(default_factory=dict)
    always_deny_rules: dict[str, list[str]] = field(default_factory=dict)
    always_ask_rules: dict[str, list[str]] = field(default_factory=dict)
    is_bypass_permissions_mode_available: bool = False
    is_auto_mode_available: bool = False
    stripped_dangerous_rules: dict[str, list[str]] | None = None
    should_avoid_permission_prompts: bool = False
    await_automated_checks_before_dialog: bool = False
    pre_plan_mode: str | None = None


def get_empty_tool_permission_context() -> ToolPermissionContext:
    """Get an empty tool permission context with defaults."""
    return ToolPermissionContext()


# ============================================================================
# Compact Progress Events
# ============================================================================


@dataclass
class CompactProgressHooksStart:
    """Hooks starting event."""

    type: Literal["hooks_start"] = "hooks_start"
    hook_type: Literal["pre_compact", "post_compact", "session_start"] = "pre_compact"


@dataclass
class CompactProgressStart:
    """Compact starting event."""

    type: Literal["compact_start"] = "compact_start"


@dataclass
class CompactProgressEnd:
    """Compact ending event."""

    type: Literal["compact_end"] = "compact_end"


CompactProgressEvent = CompactProgressHooksStart | CompactProgressStart | CompactProgressEnd

# ============================================================================
# Tool Use Context
# ============================================================================


@dataclass
class FileReadingLimits:
    """Limits for file reading operations."""

    max_tokens: int | None = None
    max_size_bytes: int | None = None


@dataclass
class GlobLimits:
    """Limits for glob operations."""

    max_results: int | None = None


@dataclass
class ToolDecision:
    """A tool decision record."""

    source: str
    decision: Literal["accept", "reject"]
    timestamp: float


@dataclass
class ToolUseContextOptions:
    """Options for tool use context."""

    commands: list[Any] = field(default_factory=list)
    debug: bool = False
    main_loop_model: str = ""
    tools: list[Any] = field(default_factory=list)
    verbose: bool = False
    thinking_config: dict[str, Any] = field(default_factory=dict)
    mcp_clients: list[Any] = field(default_factory=list)
    mcp_resources: dict[str, list[Any]] = field(default_factory=dict)
    is_non_interactive_session: bool = False
    agent_definitions: dict[str, Any] = field(default_factory=dict)
    max_budget_usd: float | None = None
    custom_system_prompt: str | None = None
    append_system_prompt: str | None = None
    query_source: str | None = None


@dataclass
class ToolUseContext:
    """Context passed to tools during execution."""

    options: ToolUseContextOptions = field(default_factory=ToolUseContextOptions)
    messages: list[Any] = field(default_factory=list)

    # State accessors (to be implemented)
    abort_controller: Any = None
    read_file_state: Any = None

    # Limits
    file_reading_limits: FileReadingLimits | None = None
    glob_limits: GlobLimits | None = None

    # Tracking
    tool_decisions: dict[str, ToolDecision] = field(default_factory=dict)
    query_tracking: QueryChainTracking | None = None

    # Agent info
    agent_id: str | None = None
    agent_type: str | None = None
    tool_use_id: str | None = None

    # Flags
    require_can_use_tool: bool = False
    user_modified: bool = False
    preserve_tool_use_results: bool = False


# ============================================================================
# Tool Progress Types
# ============================================================================


@dataclass
class ToolProgress:
    """Progress update from a tool."""

    tool_use_id: str
    data: dict[str, Any] = field(default_factory=dict)


@dataclass
class BashProgress:
    """Progress update for bash tool."""

    type: Literal["bash"] = "bash"
    stdout: str = ""
    stderr: str = ""
    exit_code: int | None = None
    is_running: bool = True


@dataclass
class AgentToolProgress:
    """Progress update for agent tool."""

    type: Literal["agent"] = "agent"
    agent_name: str = ""
    status: str = ""
    message: str = ""


@dataclass
class MCPProgress:
    """Progress update for MCP tool."""

    type: Literal["mcp"] = "mcp"
    server_name: str = ""
    tool_name: str = ""
    status: str = ""


@dataclass
class WebSearchProgress:
    """Progress update for web search tool."""

    type: Literal["web_search"] = "web_search"
    query: str = ""
    status: str = ""
    results_count: int = 0


@dataclass
class REPLToolProgress:
    """Progress update for REPL tool."""

    type: Literal["repl"] = "repl"
    language: str = ""
    output: str = ""


@dataclass
class SkillToolProgress:
    """Progress update for skill tool."""

    type: Literal["skill"] = "skill"
    skill_name: str = ""
    status: str = ""


@dataclass
class TaskOutputProgress:
    """Progress update for task output."""

    type: Literal["task_output"] = "task_output"
    task_id: str = ""
    output: str = ""


ToolProgressData = (
    BashProgress
    | AgentToolProgress
    | MCPProgress
    | WebSearchProgress
    | REPLToolProgress
    | SkillToolProgress
    | TaskOutputProgress
    | dict[str, Any]
)

# ============================================================================
# Tool Result
# ============================================================================

T = TypeVar("T")


@dataclass
class ToolResultData(Generic[T]):
    """Result from a tool execution."""

    data: T
    new_messages: list[Any] = field(default_factory=list)
    mcp_meta: dict[str, Any] | None = None


# ============================================================================
# Tool Input JSON Schema
# ============================================================================

ToolInputJSONSchema = dict[str, Any]


# ============================================================================
# Tool Matching
# ============================================================================


def tool_matches_name(
    tool: dict[str, Any],
    name: str,
) -> bool:
    """Check if a tool matches the given name (primary name or alias).

    Args:
        tool: Tool dict with 'name' and optional 'aliases' keys
        name: Name to match against

    Returns:
        True if tool matches the name
    """
    if tool.get("name") == name:
        return True

    aliases = tool.get("aliases", [])
    return name in aliases


def find_tool_by_name(
    tools: list[dict[str, Any]],
    name: str,
) -> dict[str, Any] | None:
    """Find a tool by name or alias from a list of tools.

    Args:
        tools: List of tool dicts
        name: Name to find

    Returns:
        The matching tool, or None if not found
    """
    for tool in tools:
        if tool_matches_name(tool, name):
            return tool
    return None


# ============================================================================
# Tool Defaults
# ============================================================================

TOOL_DEFAULTS = {
    "is_enabled": lambda: True,
    "is_concurrency_safe": lambda _input=None: False,
    "is_read_only": lambda _input=None: False,
    "is_destructive": lambda _input=None: False,
    "to_auto_classifier_input": lambda _input=None: "",
    "user_facing_name": lambda _input=None: "",
}


def build_tool(definition: dict[str, Any]) -> dict[str, Any]:
    """Build a complete tool from a partial definition.

    Fills in safe defaults for commonly-stubbed methods.

    Args:
        definition: Partial tool definition

    Returns:
        Complete tool with defaults filled in
    """
    tool = {**TOOL_DEFAULTS}
    tool["user_facing_name"] = lambda _input=None: definition.get("name", "")
    tool.update(definition)
    return tool


# ============================================================================
# Search/Read Command Detection
# ============================================================================


@dataclass
class SearchReadInfo:
    """Information about whether a command is a search or read operation."""

    is_search: bool = False
    is_read: bool = False
    is_list: bool = False
