"""
Teammate spawning utilities.

Functions for spawning and managing teammate processes.

Migrated from: utils/swarm/spawnUtils.ts + spawnInProcess.ts
"""

from __future__ import annotations

import os
from dataclasses import dataclass, field


@dataclass
class SpawnConfig:
    """Configuration for spawning a teammate."""

    name: str
    prompt: str
    color: str | None = None
    plan_mode_required: bool = False
    cwd: str | None = None
    env: dict[str, str] = field(default_factory=dict)


@dataclass
class SpawnResult:
    """Result of spawning a teammate."""

    success: bool
    teammate_id: str | None = None
    error: str | None = None


async def spawn_teammate(config: SpawnConfig) -> SpawnResult:
    """
    Spawn a new teammate process.

    Args:
        config: Spawn configuration

    Returns:
        SpawnResult indicating success/failure
    """
    from .constants import (
        PLAN_MODE_REQUIRED_ENV_VAR,
        TEAMMATE_COLOR_ENV_VAR,
        TEAMMATE_COMMAND_ENV_VAR,
    )

    # Get the command to run
    command = os.getenv(TEAMMATE_COMMAND_ENV_VAR)
    if not command:
        # Default to current process executable (would be Python in this case)
        import sys

        command = sys.executable

    # Build environment
    env = os.environ.copy()
    env.update(config.env)

    if config.color:
        env[TEAMMATE_COLOR_ENV_VAR] = config.color

    if config.plan_mode_required:
        env[PLAN_MODE_REQUIRED_ENV_VAR] = "true"

    env["CLAUDE_CODE_TEAMMATE_NAME"] = config.name

    try:
        # Spawn the process
        # In a full implementation, this would spawn via tmux
        import uuid

        teammate_id = str(uuid.uuid4())

        # Stub - actual implementation would spawn process
        return SpawnResult(
            success=True,
            teammate_id=teammate_id,
        )
    except Exception as e:
        return SpawnResult(
            success=False,
            error=str(e),
        )


async def spawn_in_process(config: SpawnConfig) -> SpawnResult:
    """
    Spawn a teammate in the same process (for testing/development).

    Args:
        config: Spawn configuration

    Returns:
        SpawnResult indicating success/failure
    """
    import uuid

    teammate_id = str(uuid.uuid4())

    # In-process teammate would run the query engine in a separate context
    # This is a stub for the actual implementation

    return SpawnResult(
        success=True,
        teammate_id=teammate_id,
    )


def get_teammate_command() -> str:
    """Get the command used to spawn teammates."""
    from .constants import TEAMMATE_COMMAND_ENV_VAR

    command = os.getenv(TEAMMATE_COMMAND_ENV_VAR)
    if command:
        return command

    # Default to current executable
    import sys

    return sys.executable
