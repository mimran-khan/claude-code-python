"""Built-in ``time`` command spec. Migrated from: utils/bash/specs/time.ts"""

from __future__ import annotations

from ..command_spec import Argument, CommandSpec

# ``time`` shadows stdlib; module name is time_cmd.

TIME_SPEC = CommandSpec(
    name="time",
    description="Time a command",
    args=Argument(
        name="command",
        description="Command to time",
        is_command=True,
    ),
)

__all__ = ["TIME_SPEC"]
