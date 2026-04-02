"""
Built-in command specs.

Migrated from: utils/bash/specs/index.ts
"""

from __future__ import annotations

from ..command_spec import CommandSpec
from .alias import ALIAS_SPEC
from .nohup import NOHUP_SPEC
from .pyright_spec import PYRIGHT_SPEC
from .sleep import SLEEP_SPEC
from .srun import SRUN_SPEC
from .time_cmd import TIME_SPEC
from .timeout import TIMEOUT_SPEC

BUILTIN_COMMAND_SPECS: list[CommandSpec] = [
    PYRIGHT_SPEC,
    TIMEOUT_SPEC,
    SLEEP_SPEC,
    ALIAS_SPEC,
    NOHUP_SPEC,
    TIME_SPEC,
    SRUN_SPEC,
]

__all__ = ["BUILTIN_COMMAND_SPECS"]
