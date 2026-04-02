"""Built-in ``alias`` command spec. Migrated from: utils/bash/specs/alias.ts"""

from __future__ import annotations

from ..command_spec import Argument, CommandSpec

ALIAS_SPEC = CommandSpec(
    name="alias",
    description="Create or list command aliases",
    args=Argument(
        name="definition",
        description="Alias definition in the form name=value",
        is_optional=True,
        is_variadic=True,
    ),
)

__all__ = ["ALIAS_SPEC"]
