"""
Tool registry and management.

This module handles assembling the tool pool from built-in tools,
MCP tools, and applying permission filtering.

Migrated from: tools.ts (389 lines)
"""

from __future__ import annotations

import os
from typing import TYPE_CHECKING, Any

from .tool import Tool, ToolPermissionContext, tool_matches_name

if TYPE_CHECKING:
    pass


# Tool presets
TOOL_PRESETS = ["default"]


def _tool_is_enabled(tool: Tool) -> bool:
    """True if tool exposes ``is_enabled`` and it returns truthy; default True when missing."""
    fn = getattr(tool, "is_enabled", None)
    if callable(fn):
        return bool(fn())
    return True


def parse_tool_preset(preset: str) -> str | None:
    """Parse a tool preset string."""
    preset_lower = preset.lower()
    if preset_lower not in TOOL_PRESETS:
        return None
    return preset_lower


# Tools that are disallowed for agents
ALL_AGENT_DISALLOWED_TOOLS: set[str] = {
    "SendMessage",
    "TeamCreate",
    "TeamDelete",
    "TodoWrite",
}

CUSTOM_AGENT_DISALLOWED_TOOLS: set[str] = {
    "TaskCreate",
    "TaskUpdate",
    "TaskList",
    "TaskGet",
    "TaskStop",
    "TaskOutput",
}

ASYNC_AGENT_ALLOWED_TOOLS: set[str] = {
    "Bash",
    "Read",
    "Edit",
    "Write",
    "Glob",
    "Grep",
    "WebFetch",
    "WebSearch",
    "NotebookEdit",
    "Skill",
    "Config",
    "SendMessage",
    "Brief",
}

COORDINATOR_MODE_ALLOWED_TOOLS: set[str] = {
    "Task",
    "TaskStop",
    "TaskOutput",
    "SendMessage",
    "Read",
    "Glob",
    "Grep",
    "Brief",
}

# REPL-only tools (hidden when REPL is enabled since they're wrapped)
REPL_TOOL_NAME = "REPL"
REPL_ONLY_TOOLS: set[str] = {
    "Bash",
    "Read",
    "Edit",
    "Write",
    "Glob",
    "Grep",
}


def _is_env_truthy(value: str | None) -> bool:
    """Check if an environment variable is truthy."""
    if not value:
        return False
    return value.lower() in ("true", "1", "yes")


def _is_simple_mode() -> bool:
    """Check if simple mode is enabled."""
    return _is_env_truthy(os.getenv("CLAUDE_CODE_SIMPLE"))


def _is_repl_mode_enabled() -> bool:
    """Check if REPL mode is enabled."""
    return _is_env_truthy(os.getenv("CLAUDE_CODE_REPL_MODE"))


def _is_worktree_mode_enabled() -> bool:
    """Check if worktree mode is enabled."""
    return _is_env_truthy(os.getenv("CLAUDE_CODE_WORKTREE_MODE"))


def _is_agent_swarms_enabled() -> bool:
    """Check if agent swarms are enabled."""
    return _is_env_truthy(os.getenv("CLAUDE_CODE_AGENT_SWARMS"))


def _is_tool_search_enabled() -> bool:
    """Check if tool search is enabled."""
    return _is_env_truthy(os.getenv("CLAUDE_CODE_TOOL_SEARCH"))


def _is_todo_v2_enabled() -> bool:
    """Check if Todo v2 (Tasks) is enabled."""
    return _is_env_truthy(os.getenv("CLAUDE_CODE_TODO_V2"))


def _has_embedded_search_tools() -> bool:
    """Check if embedded search tools are available."""
    return _is_env_truthy(os.getenv("CLAUDE_CODE_EMBEDDED_SEARCH"))


def _is_coordinator_mode() -> bool:
    """Check if coordinator mode is active."""
    return _is_env_truthy(os.getenv("CLAUDE_CODE_COORDINATOR_MODE"))


def get_deny_rule_for_tool(
    permission_context: ToolPermissionContext,
    tool: Tool | dict[str, Any],
) -> dict[str, Any] | None:
    """
    Check if a tool has a blanket deny rule.

    A tool is denied if there's a deny rule matching its name with no
    ruleContent (i.e., a blanket deny for that tool).
    """
    if isinstance(tool, dict):
        tool_name = tool.get("name", "")
        mcp_info = tool.get("mcpInfo")
    else:
        tool_name = tool.name
        mcp_info = getattr(tool, "mcp_info", None)

    # Check direct tool name deny rules
    for _source, rules in permission_context.always_deny_rules.items():
        for rule in rules:
            if isinstance(rule, dict):
                pattern = rule.get("pattern", rule.get("toolName", ""))
                rule_content = rule.get("ruleContent")
            else:
                pattern = str(rule)
                rule_content = None

            # Blanket deny (no specific rule content)
            if not rule_content:
                if pattern == tool_name:
                    return rule if isinstance(rule, dict) else {"pattern": pattern}

                # MCP server prefix matching
                if mcp_info and pattern.startswith("mcp__"):
                    server_prefix = pattern.replace("mcp__", "").replace("__", "/")
                    if mcp_info.get("serverName", "").startswith(server_prefix):
                        return rule if isinstance(rule, dict) else {"pattern": pattern}

    return None


def filter_tools_by_deny_rules(
    tools: list[Tool],
    permission_context: ToolPermissionContext,
) -> list[Tool]:
    """
    Filter out tools that are blanket-denied by the permission context.

    A tool is filtered out if there's a deny rule matching its name with no
    ruleContent (i.e., a blanket deny for that tool).
    """
    return [tool for tool in tools if get_deny_rule_for_tool(permission_context, tool) is None]


# Lazy tool imports to avoid circular dependencies
_base_tools: list[Tool] | None = None


def _get_all_base_tools_impl() -> list[Tool]:
    """
    Get all base tools lazily.

    This avoids circular imports by importing tools only when needed.
    """
    global _base_tools
    if _base_tools is not None:
        return _base_tools

    tools: list[Tool] = []

    # Import tools lazily
    try:
        from ..tools.agent_tool.agent_tool import AgentTool

        tools.append(AgentTool())
    except (ImportError, TypeError):
        pass

    try:
        from ..tools.task_output import TaskOutputTool

        tools.append(TaskOutputTool())
    except (ImportError, TypeError):
        pass

    try:
        from ..tools.bash_tool.bash_tool import BashTool

        tools.append(BashTool())
    except (ImportError, TypeError):
        pass

    # Only add Glob/Grep if embedded search tools aren't available
    if not _has_embedded_search_tools():
        try:
            from ..tools.glob_tool.glob_tool import GlobTool

            tools.append(GlobTool())
        except (ImportError, TypeError):
            pass

        try:
            from ..tools.grep_tool.grep_tool import GrepTool

            tools.append(GrepTool())
        except (ImportError, TypeError):
            pass

    try:
        from ..tools.file_read_tool.file_read_tool import FileReadTool

        tools.append(FileReadTool())
    except (ImportError, TypeError):
        pass

    try:
        from ..tools.file_edit_tool.file_edit_tool import FileEditTool

        tools.append(FileEditTool())
    except (ImportError, TypeError):
        pass

    try:
        from ..tools.file_write_tool.file_write_tool import FileWriteTool

        tools.append(FileWriteTool())
    except (ImportError, TypeError):
        pass

    try:
        from ..tools.notebook_edit import NotebookEditTool

        tools.append(NotebookEditTool())
    except (ImportError, TypeError):
        pass

    try:
        from ..tools.web_fetch import WebFetchTool

        tools.append(WebFetchTool())
    except (ImportError, TypeError):
        pass

    try:
        from ..tools.web_search import WebSearchTool

        tools.append(WebSearchTool())
    except (ImportError, TypeError):
        pass

    try:
        from ..tools.todo_write import TodoWriteTool

        tools.append(TodoWriteTool())
    except (ImportError, TypeError):
        pass

    try:
        from ..tools.ask_user_question import AskUserQuestionTool

        tools.append(AskUserQuestionTool())
    except (ImportError, TypeError):
        pass

    try:
        from ..tools.skill import SkillTool

        tools.append(SkillTool())
    except (ImportError, TypeError):
        pass

    try:
        from ..tools.brief import BriefTool

        tools.append(BriefTool())
    except (ImportError, TypeError):
        pass

    # Task tools (Todo v2)
    if _is_todo_v2_enabled():
        try:
            from ..tools.task_create import TaskCreateTool
            from ..tools.task_get import TaskGetTool
            from ..tools.task_list import TaskListTool
            from ..tools.task_update import TaskUpdateTool

            tools.extend([TaskCreateTool(), TaskGetTool(), TaskUpdateTool(), TaskListTool()])
        except (ImportError, TypeError):
            pass

    # MCP resource tools
    try:
        from ..tools.list_mcp_resources import ListMcpResourcesTool

        tools.append(ListMcpResourcesTool())
    except (ImportError, TypeError):
        pass

    try:
        from ..tools.read_mcp_resource import ReadMcpResourceTool

        tools.append(ReadMcpResourceTool())
    except (ImportError, TypeError):
        pass

    # Tool search
    if _is_tool_search_enabled():
        try:
            from ..tools.tool_search import ToolSearchTool

            tools.append(ToolSearchTool())
        except (ImportError, TypeError):
            pass

    _base_tools = tools
    return tools


def get_all_base_tools() -> list[Tool]:
    """
    Get the complete list of all tools available in the current environment.

    This is the source of truth for ALL tools.
    """
    return _get_all_base_tools_impl()


def get_tools_for_default_preset() -> list[str]:
    """
    Get the list of tool names for the default preset.

    Filters out tools that are disabled via isEnabled() check.
    """
    tools = get_all_base_tools()
    return [tool.name for tool in tools if tool.is_enabled()]


def get_tools(permission_context: ToolPermissionContext) -> list[Tool]:
    """
    Get tools available for the given permission context.

    Respects mode filtering (simple mode, REPL mode, etc.) and deny rules.
    """
    # Simple mode: only Bash, Read, and Edit tools
    if _is_simple_mode():
        simple_tools: list[Tool] = []

        if _is_repl_mode_enabled():
            # REPL wraps Bash/Read/Edit inside the VM
            try:
                from ..tools.repl import REPLTool

                simple_tools.append(REPLTool())
            except (ImportError, TypeError):
                pass
        else:
            try:
                from ..tools.bash_tool.bash_tool import BashTool

                simple_tools.append(BashTool())
            except (ImportError, TypeError):
                pass

            try:
                from ..tools.file_read_tool.file_read_tool import FileReadTool

                simple_tools.append(FileReadTool())
            except (ImportError, TypeError):
                pass

            try:
                from ..tools.file_edit_tool.file_edit_tool import FileEditTool

                simple_tools.append(FileEditTool())
            except (ImportError, TypeError):
                pass

        # Coordinator mode additions
        if _is_coordinator_mode():
            try:
                from ..tools.agent_tool.agent_tool import AgentTool
                from ..tools.send_message import SendMessageTool
                from ..tools.task_stop import TaskStopTool

                simple_tools.extend([AgentTool(), TaskStopTool(), SendMessageTool()])
            except (ImportError, TypeError):
                pass

        return filter_tools_by_deny_rules(simple_tools, permission_context)

    # Get all base tools
    special_tool_names = {
        "ListMcpResources",
        "ReadMcpResource",
        "StructuredOutput",
    }

    tools = [tool for tool in get_all_base_tools() if tool.name not in special_tool_names]

    # Filter by deny rules
    allowed_tools = filter_tools_by_deny_rules(tools, permission_context)

    # Hide REPL-only tools when REPL is enabled
    if _is_repl_mode_enabled():
        repl_enabled = any(tool_matches_name(tool, REPL_TOOL_NAME) for tool in allowed_tools)
        if repl_enabled:
            allowed_tools = [tool for tool in allowed_tools if tool.name not in REPL_ONLY_TOOLS]

    # Filter by enabled status
    return [tool for tool in allowed_tools if _tool_is_enabled(tool)]


def assemble_tool_pool(
    permission_context: ToolPermissionContext,
    mcp_tools: list[Tool],
) -> list[Tool]:
    """
    Assemble the full tool pool for a given permission context and MCP tools.

    This is the single source of truth for combining built-in tools with MCP tools.

    The function:
    1. Gets built-in tools via get_tools() (respects mode filtering)
    2. Filters MCP tools by deny rules
    3. Deduplicates by tool name (built-in tools take precedence)
    """
    built_in_tools = get_tools(permission_context)

    # Filter MCP tools by deny rules
    allowed_mcp_tools = filter_tools_by_deny_rules(mcp_tools, permission_context)

    # Sort each partition for prompt-cache stability
    def by_name(t: Tool) -> str:
        return t.name

    sorted_builtins = sorted(built_in_tools, key=by_name)
    sorted_mcp = sorted(allowed_mcp_tools, key=by_name)

    # Deduplicate by name (built-ins win)
    seen_names: set[str] = set()
    result: list[Tool] = []

    for tool in sorted_builtins:
        if tool.name not in seen_names:
            seen_names.add(tool.name)
            result.append(tool)

    for tool in sorted_mcp:
        if tool.name not in seen_names:
            seen_names.add(tool.name)
            result.append(tool)

    return result


def get_merged_tools(
    permission_context: ToolPermissionContext,
    mcp_tools: list[Tool],
) -> list[Tool]:
    """
    Get all tools including both built-in tools and MCP tools.

    This is the preferred function when you need the complete tools list.
    """
    built_in_tools = get_tools(permission_context)
    return [*built_in_tools, *mcp_tools]
