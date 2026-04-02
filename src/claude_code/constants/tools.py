"""Tool availability constants for different agent contexts."""

import os

# Tool name constants - these would normally be imported from tool modules
TASK_OUTPUT_TOOL_NAME = "task_output"
EXIT_PLAN_MODE_V2_TOOL_NAME = "exit_plan_mode_v2"
ENTER_PLAN_MODE_TOOL_NAME = "enter_plan_mode"
AGENT_TOOL_NAME = "Task"
ASK_USER_QUESTION_TOOL_NAME = "AskQuestion"
TASK_STOP_TOOL_NAME = "task_stop"
FILE_READ_TOOL_NAME = "Read"
WEB_SEARCH_TOOL_NAME = "WebSearch"
TODO_WRITE_TOOL_NAME = "TodoWrite"
GREP_TOOL_NAME = "Grep"
WEB_FETCH_TOOL_NAME = "WebFetch"
GLOB_TOOL_NAME = "Glob"
SHELL_TOOL_NAME = "Shell"
FILE_EDIT_TOOL_NAME = "Edit"
FILE_WRITE_TOOL_NAME = "Write"
NOTEBOOK_EDIT_TOOL_NAME = "EditNotebook"
SKILL_TOOL_NAME = "Skill"
SYNTHETIC_OUTPUT_TOOL_NAME = "synthetic_output"
TOOL_SEARCH_TOOL_NAME = "tool_search"
ENTER_WORKTREE_TOOL_NAME = "enter_worktree"
EXIT_WORKTREE_TOOL_NAME = "exit_worktree"
SEND_MESSAGE_TOOL_NAME = "send_message"
TASK_CREATE_TOOL_NAME = "task_create"
TASK_GET_TOOL_NAME = "task_get"
TASK_LIST_TOOL_NAME = "task_list"
TASK_UPDATE_TOOL_NAME = "task_update"
CRON_CREATE_TOOL_NAME = "cron_create"
CRON_DELETE_TOOL_NAME = "cron_delete"
CRON_LIST_TOOL_NAME = "cron_list"
WORKFLOW_TOOL_NAME = "workflow"

# Shell tool names
SHELL_TOOL_NAMES = frozenset([SHELL_TOOL_NAME])

# All tools disallowed for any agent
_base_disallowed = [
    TASK_OUTPUT_TOOL_NAME,
    EXIT_PLAN_MODE_V2_TOOL_NAME,
    ENTER_PLAN_MODE_TOOL_NAME,
    ASK_USER_QUESTION_TOOL_NAME,
    TASK_STOP_TOOL_NAME,
]

# Allow Agent tool for agents when user is ant (enables nested agents)
if os.environ.get("USER_TYPE") != "ant":
    _base_disallowed.append(AGENT_TOOL_NAME)

ALL_AGENT_DISALLOWED_TOOLS = frozenset(_base_disallowed)

CUSTOM_AGENT_DISALLOWED_TOOLS = frozenset(_base_disallowed)

# Async Agent Tool Availability Status (Source of Truth)
ASYNC_AGENT_ALLOWED_TOOLS = frozenset(
    [
        FILE_READ_TOOL_NAME,
        WEB_SEARCH_TOOL_NAME,
        TODO_WRITE_TOOL_NAME,
        GREP_TOOL_NAME,
        WEB_FETCH_TOOL_NAME,
        GLOB_TOOL_NAME,
        SHELL_TOOL_NAME,
        FILE_EDIT_TOOL_NAME,
        FILE_WRITE_TOOL_NAME,
        NOTEBOOK_EDIT_TOOL_NAME,
        SKILL_TOOL_NAME,
        SYNTHETIC_OUTPUT_TOOL_NAME,
        TOOL_SEARCH_TOOL_NAME,
        ENTER_WORKTREE_TOOL_NAME,
        EXIT_WORKTREE_TOOL_NAME,
    ]
)

# Tools allowed only for in-process teammates (not general async agents)
IN_PROCESS_TEAMMATE_ALLOWED_TOOLS = frozenset(
    [
        TASK_CREATE_TOOL_NAME,
        TASK_GET_TOOL_NAME,
        TASK_LIST_TOOL_NAME,
        TASK_UPDATE_TOOL_NAME,
        SEND_MESSAGE_TOOL_NAME,
        CRON_CREATE_TOOL_NAME,
        CRON_DELETE_TOOL_NAME,
        CRON_LIST_TOOL_NAME,
    ]
)

# Tools allowed in coordinator mode - only output and agent management tools
COORDINATOR_MODE_ALLOWED_TOOLS = frozenset(
    [
        AGENT_TOOL_NAME,
        TASK_STOP_TOOL_NAME,
        SEND_MESSAGE_TOOL_NAME,
        SYNTHETIC_OUTPUT_TOOL_NAME,
    ]
)
