"""
Shared validation schemas (settings hooks, etc.).

Migrated from: schemas/hooks.ts
"""

from .hook_schemas import (
    AgentHook,
    BashCommandHook,
    HookCommand,
    HookMatcher,
    HooksSettings,
    HttpHook,
    PromptHook,
    parse_hook_command,
    parse_hooks_settings,
)

__all__ = [
    "AgentHook",
    "BashCommandHook",
    "HookCommand",
    "HookMatcher",
    "HooksSettings",
    "HttpHook",
    "PromptHook",
    "parse_hook_command",
    "parse_hooks_settings",
]
