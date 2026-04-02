"""
State selectors.

Migrated from: state/selectors.ts
"""

from typing import Any, Literal

from .app_state import AppState


def _is_in_process_teammate(task: Any) -> bool:
    return isinstance(task, dict) and task.get("type") == "in_process_teammate"


def get_viewed_teammate_task(
    app_state: AppState,
) -> dict[str, Any] | None:
    """Return in-process teammate task when its transcript is focused."""
    task_id = app_state.viewing_agent_task_id
    if not task_id:
        return None
    task = (app_state.tasks or {}).get(task_id)
    if not _is_in_process_teammate(task):
        return None
    return task


ActiveAgentForInput = Literal["leader"] | dict[str, Any]


def get_active_agent_for_input(app_state: AppState) -> ActiveAgentForInput:
    """Route target for user input (leader vs viewed teammate vs named local agent)."""
    viewed = get_viewed_teammate_task(app_state)
    if viewed is not None:
        return {"type": "viewed", "task": viewed}
    task_id = app_state.viewing_agent_task_id
    if task_id:
        task = (app_state.tasks or {}).get(task_id)
        if isinstance(task, dict) and task.get("type") == "local_agent":
            return {"type": "named_agent", "task": task}
    return "leader"


def get_current_agent_id(state: AppState) -> str | None:
    """Get the current agent ID."""
    return state.current_agent_id


def get_messages(state: AppState) -> list[Any]:
    """Get all messages."""
    return state.messages


def get_tool_permission_context(state: AppState) -> dict[str, Any]:
    """Get the tool permission context."""
    return state.tool_permission_context


def get_settings(state: AppState) -> Any:
    """Get current settings."""
    return state.settings


def get_is_loading(state: AppState) -> bool:
    """Check if currently loading."""
    return state.is_loading


def get_is_paused(state: AppState) -> bool:
    """Check if paused."""
    return state.is_paused


def get_speculation_state(state: AppState) -> Any:
    """Get speculation state."""
    return state.speculation


def get_tasks(state: AppState) -> dict[str, Any]:
    """Get all tasks."""
    return state.tasks


def get_notifications(state: AppState) -> list[Any]:
    """Get all notifications."""
    return state.notifications


def get_mcp_state(state: AppState) -> Any:
    """Get MCP connection state."""
    return state.mcp


def get_loaded_plugins(state: AppState) -> list[Any]:
    """Get loaded plugins."""
    return state.loaded_plugins
