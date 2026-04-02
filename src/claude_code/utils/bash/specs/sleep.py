"""Built-in ``sleep`` command spec. Migrated from: utils/bash/specs/sleep.ts"""

from __future__ import annotations

from ..command_spec import Argument, CommandSpec

SLEEP_SPEC = CommandSpec(
    name="sleep",
    description="Delay for a specified amount of time",
    args=Argument(
        name="duration",
        description="Duration to sleep (seconds or with suffix like 5s, 2m, 1h)",
        is_optional=False,
    ),
)

__all__ = ["SLEEP_SPEC"]
