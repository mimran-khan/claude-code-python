"""Swarm session constants. Migrated from: utils/swarm/constants.ts"""

from __future__ import annotations

import os

TEAM_LEAD_NAME = "team-lead"
SWARM_SESSION_NAME = "claude-swarm"
SWARM_VIEW_WINDOW_NAME = "swarm-view"
TMUX_COMMAND = "tmux"
HIDDEN_SESSION_NAME = "claude-hidden"
TEAMMATE_COMMAND_ENV_VAR = "CLAUDE_CODE_TEAMMATE_COMMAND"
TEAMMATE_COLOR_ENV_VAR = "CLAUDE_CODE_AGENT_COLOR"
PLAN_MODE_REQUIRED_ENV_VAR = "CLAUDE_CODE_PLAN_MODE_REQUIRED"


def get_swarm_socket_name() -> str:
    return f"claude-swarm-{os.getpid()}"
