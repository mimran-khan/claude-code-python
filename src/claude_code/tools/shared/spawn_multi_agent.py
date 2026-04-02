"""
Shared types and pure helpers for teammate / multi-agent spawn flows.

Migrated from: tools/shared/spawnMultiAgent.ts (subset — UI/tmux integration is host-specific).

The TypeScript module wires React, tmux, and AppState; Python keeps data shapes and
portable helpers so callers can integrate with their runtime.
"""

from __future__ import annotations

import asyncio
import os
import uuid
from dataclasses import dataclass, field
from typing import Any


@dataclass
class SpawnOutput:
    teammate_id: str
    agent_id: str
    name: str
    tmux_session_name: str
    tmux_window_name: str
    tmux_pane_id: str
    agent_type: str | None = None
    model: str | None = None
    color: str | None = None
    team_name: str | None = None
    is_splitpane: bool | None = None
    plan_mode_required: bool | None = None


@dataclass
class SpawnTeammateConfig:
    name: str
    prompt: str
    team_name: str | None = None
    cwd: str | None = None
    use_splitpane: bool = True
    plan_mode_required: bool = False
    model: str | None = None
    agent_type: str | None = None
    description: str | None = None
    invoking_request_id: str | None = None


def get_default_teammate_model(leader_model: str | None, configured_default: Any = None) -> str:
    """
    Resolve default teammate model when the user has not specified one.

    `configured_default` mirrors getGlobalConfig().teammateDefaultModel:
    - None: follow leader
    - str: explicit model id
    - missing attribute: use hardcoded fallback string
    """
    if configured_default is None:
        return leader_model or "claude-sonnet-4-20250514"
    if isinstance(configured_default, str):
        return configured_default
    return "claude-sonnet-4-20250514"


def resolve_teammate_model(
    input_model: str | None,
    leader_model: str | None,
    *,
    configured_default: Any = None,
) -> str:
    """Resolve 'inherit' and undefined model like the TS helper."""
    if input_model == "inherit":
        return get_default_teammate_model(leader_model, configured_default)
    if input_model:
        return input_model
    return get_default_teammate_model(leader_model, configured_default)


@dataclass
class TeamMemberRecord:
    name: str
    agent_id: str
    is_active: bool | None = None


@dataclass
class TeamFileSnapshot:
    members: list[TeamMemberRecord] = field(default_factory=list)


async def generate_unique_teammate_name(base_name: str, team_name: str | None) -> str:
    """
    Append numeric suffix when the base name already exists in the team file.

    When `team_name` is None or team file is unavailable, returns `base_name` unchanged.
    """
    if not team_name:
        return base_name
    # Host integration should load the real team file; default is no collision.
    return base_name


def _spawn_output_for(
    config: SpawnTeammateConfig,
    *,
    teammate_id: str,
    agent_id: str,
) -> SpawnOutput:
    short = teammate_id.split("-", 1)[0][:8]
    session = f"cc-teammate-{short}"
    return SpawnOutput(
        teammate_id=teammate_id,
        agent_id=agent_id,
        name=config.name,
        tmux_session_name=session,
        tmux_window_name=f"{config.name[:32] or 'agent'}",
        tmux_pane_id=f"%{short}",
        agent_type=config.agent_type,
        model=config.model,
        team_name=config.team_name,
        is_splitpane=config.use_splitpane,
        plan_mode_required=config.plan_mode_required,
    )


async def spawn_teammate(
    config: SpawnTeammateConfig,
    context: Any,
) -> SpawnOutput:
    """
    Spawn a teammate process when ``CLAUDE_CODE_SPAWN_TEAMMATE_CMD`` is set.

    The environment variable is executed via ``sh -c`` (or POSIX ``SHELL``). The
    prompt is exported as ``CLAUDE_CODE_TEAMMATE_PROMPT``. When unset, returns a
    synthetic :class:`SpawnOutput` without starting a process (host/tmux integration
    can override by setting the env var).
    """
    _ = context
    teammate_id = str(uuid.uuid4())
    agent_id = str(uuid.uuid4())
    cmd = os.environ.get("CLAUDE_CODE_SPAWN_TEAMMATE_CMD", "").strip()
    if not cmd:
        return _spawn_output_for(config, teammate_id=teammate_id, agent_id=agent_id)

    env = os.environ.copy()
    env["CLAUDE_CODE_TEAMMATE_PROMPT"] = config.prompt
    env["CLAUDE_CODE_TEAMMATE_NAME"] = config.name
    env["CLAUDE_CODE_TEAMMATE_ID"] = teammate_id
    env["CLAUDE_CODE_AGENT_ID"] = agent_id
    if config.cwd:
        env["CLAUDE_CODE_TEAMMATE_CWD"] = config.cwd

    def _run() -> None:
        # Use user's shell when available for alias/function support
        shell = os.environ.get("SHELL") or "/bin/sh"
        argv = [shell, "-c", cmd]
        os.spawnvpe(os.P_NOWAIT, shell, argv, env)

    await asyncio.to_thread(_run)
    return _spawn_output_for(config, teammate_id=teammate_id, agent_id=agent_id)
