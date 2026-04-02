"""Built-in ``timeout`` command spec. Migrated from: utils/bash/specs/timeout.ts"""

from __future__ import annotations

from ..command_spec import Argument, CommandSpec

TIMEOUT_SPEC = CommandSpec(
    name="timeout",
    description="Run a command with a time limit",
    args=[
        Argument(
            name="duration",
            description="Duration to wait before timing out (e.g., 10, 5s, 2m)",
            is_optional=False,
        ),
        Argument(
            name="command",
            description="Command to run",
            is_command=True,
        ),
    ],
)

__all__ = ["TIMEOUT_SPEC"]
