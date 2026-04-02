"""
Application state management.

Migrated from: state/*.ts
"""

from .app_state import (
    IDLE_SPECULATION_STATE,
    AppState,
    CompletionBoundary,
    SpeculationResult,
    SpeculationState,
    create_initial_app_state,
)
from .on_app_state_change import (
    AppStateChangeHooks,
    external_metadata_to_app_state,
    on_change_app_state,
    set_app_state_change_hooks,
)
from .selectors import (
    ActiveAgentForInput,
    get_active_agent_for_input,
    get_current_agent_id,
    get_messages,
    get_tool_permission_context,
    get_viewed_teammate_task,
)
from .store import (
    Store,
    Subscriber,
    create_store,
)
from .teammate_view import (
    enter_teammate_view,
    exit_teammate_view,
    stop_or_dismiss_agent,
)

__all__ = [
    # Store
    "Store",
    "create_store",
    "Subscriber",
    # AppState
    "AppState",
    "IDLE_SPECULATION_STATE",
    "CompletionBoundary",
    "SpeculationState",
    "SpeculationResult",
    "create_initial_app_state",
    # Selectors
    "get_current_agent_id",
    "get_messages",
    "get_tool_permission_context",
    "get_viewed_teammate_task",
    "get_active_agent_for_input",
    "ActiveAgentForInput",
    "enter_teammate_view",
    "exit_teammate_view",
    "stop_or_dismiss_agent",
    "on_change_app_state",
    "external_metadata_to_app_state",
    "AppStateChangeHooks",
    "set_app_state_change_hooks",
]
