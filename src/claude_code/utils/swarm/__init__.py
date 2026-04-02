"""Teammate / swarm utilities. Migrated from: utils/swarm/*.ts (skeleton)."""

from __future__ import annotations

from . import backends
from .constants import (
    HIDDEN_SESSION_NAME,
    PLAN_MODE_REQUIRED_ENV_VAR,
    SWARM_SESSION_NAME,
    SWARM_VIEW_WINDOW_NAME,
    TEAM_LEAD_NAME,
    TEAMMATE_COLOR_ENV_VAR,
    TEAMMATE_COMMAND_ENV_VAR,
    TMUX_COMMAND,
    get_swarm_socket_name,
)
from .types import BackendType, CreatePaneResult, PaneBackendType, PaneId

__all__ = [
    "BackendType",
    "CreatePaneResult",
    "HIDDEN_SESSION_NAME",
    "PLAN_MODE_REQUIRED_ENV_VAR",
    "PaneBackendType",
    "PaneId",
    "SWARM_SESSION_NAME",
    "SWARM_VIEW_WINDOW_NAME",
    "TEAM_LEAD_NAME",
    "TEAMMATE_COLOR_ENV_VAR",
    "TEAMMATE_COMMAND_ENV_VAR",
    "TMUX_COMMAND",
    "backends",
    "get_swarm_socket_name",
]
