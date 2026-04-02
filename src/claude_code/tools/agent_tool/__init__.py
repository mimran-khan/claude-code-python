"""
Agent Tool.

Spawn and manage subagents for complex tasks.

Migrated from: tools/AgentTool/*.ts (12 files)
"""

from .agent_display import (
    AGENT_SOURCE_GROUPS,
    resolve_agent_model_display,
    resolve_agent_overrides,
)
from .agent_memory import (
    AgentMemory,
    AgentMemoryEntry,
    AgentMemoryManager,
    AgentMemorySnapshot,
    get_agent_memory,
    get_memory_manager,
)
from .agent_memory_snapshot import (
    check_agent_memory_snapshot,
    get_agent_memory_dir,
    get_snapshot_dir_for_agent,
    initialize_from_snapshot,
)
from .agent_tool import (
    AgentInput,
    AgentOutput,
    AgentTool,
)
from .builtin_agents import (
    EXPLORE_AGENT,
    GENERAL_PURPOSE_AGENT,
    PLAN_AGENT,
    SHELL_AGENT,
    VERIFICATION_AGENT,
    AgentDefinition,
    get_agent_by_type,
    get_builtin_agents,
    is_builtin_agent,
)
from .constants import (
    AGENT_TOOL_NAME,
    LEGACY_AGENT_TOOL_NAME,
    ONE_SHOT_BUILTIN_AGENT_TYPES,
    VERIFICATION_AGENT_TYPE,
    is_one_shot_agent,
)
from .fork_subagent import (
    FORK_AGENT,
    is_fork_subagent_enabled,
    is_in_fork_child,
)
from .load_agents_dir import (
    AgentDefinitionsResult,
    clear_agent_definitions_cache,
    filter_agents_by_mcp_requirements,
    get_active_agents_from_list,
    get_agent_definitions_with_overrides,
    has_required_mcp_servers,
)
from .run_agent import (
    AgentContext,
    AgentResult,
    cancel_agent,
    create_agent_id,
    resume_agent,
    run_agent,
)

__all__ = [
    # Tool
    "AgentTool",
    "AgentInput",
    "AgentOutput",
    # Constants
    "AGENT_TOOL_NAME",
    "LEGACY_AGENT_TOOL_NAME",
    "VERIFICATION_AGENT_TYPE",
    "ONE_SHOT_BUILTIN_AGENT_TYPES",
    "is_one_shot_agent",
    # Built-in agents
    "AgentDefinition",
    "get_builtin_agents",
    "get_agent_by_type",
    "is_builtin_agent",
    "GENERAL_PURPOSE_AGENT",
    "EXPLORE_AGENT",
    "PLAN_AGENT",
    "SHELL_AGENT",
    "VERIFICATION_AGENT",
    # Run agent
    "run_agent",
    "resume_agent",
    "cancel_agent",
    "create_agent_id",
    "AgentContext",
    "AgentResult",
    # Memory
    "AgentMemory",
    "AgentMemoryEntry",
    "AgentMemorySnapshot",
    "AgentMemoryManager",
    "get_memory_manager",
    "get_agent_memory",
    # Load agents / definitions
    "AgentDefinitionsResult",
    "clear_agent_definitions_cache",
    "get_active_agents_from_list",
    "get_agent_definitions_with_overrides",
    "has_required_mcp_servers",
    "filter_agents_by_mcp_requirements",
    # Memory snapshots
    "check_agent_memory_snapshot",
    "get_agent_memory_dir",
    "get_snapshot_dir_for_agent",
    "initialize_from_snapshot",
    # Fork experiment
    "FORK_AGENT",
    "is_fork_subagent_enabled",
    "is_in_fork_child",
    # Display
    "AGENT_SOURCE_GROUPS",
    "resolve_agent_overrides",
    "resolve_agent_model_display",
]
