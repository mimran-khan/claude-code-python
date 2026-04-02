"""
Migrated from: commands/createMovedToPluginCommand.ts

Factory helpers for slash commands that delegate to marketplace plugins for Ant users
while keeping an inline prompt fallback elsewhere.
"""

from __future__ import annotations

import os
from collections.abc import Awaitable, Callable

from claude_code.commands.pr_comments.moved_plugin import PromptTextBlock


def plugin_install_instructions(plugin_name: str, plugin_command: str) -> str:
    return f"""This command has been moved to a plugin. Tell the user:

1. To install the plugin, run:
   claude plugin install {plugin_name}@claude-code-marketplace

2. After installation, use /{plugin_name}:{plugin_command} to run this command

3. For more information, see: https://github.com/anthropics/claude-code-marketplace/blob/main/{plugin_name}/README.md

Do not attempt to run the command. Simply inform the user about the plugin installation."""


async def resolve_moved_to_plugin_prompt(
    *,
    plugin_name: str,
    plugin_command: str,
    get_prompt_while_marketplace_is_private: Callable[[str], Awaitable[list[PromptTextBlock]]],
    args: str,
) -> list[PromptTextBlock]:
    """Match createMovedToPluginCommand.getPromptForCommand branching on USER_TYPE."""

    if os.environ.get("USER_TYPE") == "ant":
        return [PromptTextBlock(text=plugin_install_instructions(plugin_name, plugin_command))]
    return await get_prompt_while_marketplace_is_private(args)


__all__ = [
    "plugin_install_instructions",
    "resolve_moved_to_plugin_prompt",
]
