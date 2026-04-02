"""
Defense-in-depth bash safety checks (brace expansion, command substitution).

Migrated from: tools/BashTool/bashSecurity.ts

Heavy pattern tables remain in TypeScript; Python delegates to :mod:`.validation`.
"""

from __future__ import annotations

from .validation import is_safe_bash_command, validate_bash_command


def bash_command_is_safe_deprecated(command: str) -> bool:
    return is_safe_bash_command(command)


async def bash_command_is_safe_async_deprecated(command: str) -> bool:
    return validate_bash_command(command).is_safe


__all__ = ["bash_command_is_safe_async_deprecated", "bash_command_is_safe_deprecated"]
