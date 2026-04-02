"""Built-in ``nohup`` command spec. Migrated from: utils/bash/specs/nohup.ts"""

from __future__ import annotations

from ..command_spec import Argument, CommandSpec

NOHUP_SPEC = CommandSpec(
    name="nohup",
    description="Run a command immune to hangups",
    args=Argument(
        name="command",
        description="Command to run with nohup",
        is_command=True,
    ),
)

__all__ = ["NOHUP_SPEC"]
