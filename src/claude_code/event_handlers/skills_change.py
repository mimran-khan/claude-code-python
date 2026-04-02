"""
Reload commands when skills or GrowthBook refresh.

Migrated from: hooks/useSkillsChange.ts
"""

from __future__ import annotations

from collections.abc import Awaitable, Callable


async def reload_commands_after_skill_change(
    cwd: str | None,
    *,
    clear_commands_cache: Callable[[], None],
    get_commands: Callable[[str], Awaitable[list[object]]],
    on_commands_change: Callable[[list[object]], None],
) -> None:
    if not cwd:
        return
    clear_commands_cache()
    cmds = await get_commands(cwd)
    on_commands_change(cmds)


async def reload_commands_after_growthbook_memo_clear(
    cwd: str | None,
    *,
    clear_command_memoization_caches: Callable[[], None],
    get_commands: Callable[[str], Awaitable[list[object]]],
    on_commands_change: Callable[[list[object]], None],
) -> None:
    if not cwd:
        return
    clear_command_memoization_caches()
    cmds = await get_commands(cwd)
    on_commands_change(cmds)
