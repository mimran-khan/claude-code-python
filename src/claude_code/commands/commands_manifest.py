"""
Central command list and helpers.

Migrated from: commands.ts (registry portions: COMMANDS list, findCommand, …)
"""

from __future__ import annotations

import os
from collections.abc import Iterable
from functools import lru_cache

from claude_code.commands.spec import (
    CommandSpec,
    resolve_description,
    resolve_enabled,
    resolve_hidden,
)


def get_command_name(spec: CommandSpec) -> str:
    return spec.name


def meets_availability_requirement(spec: CommandSpec) -> bool:
    """
    Filter commands by declared availability (auth / provider).

    Full parity requires auth helpers from utils/auth (ported).
    """
    if not spec.availability:
        return True
    # Stub: allow all until auth wiring is complete
    return True


def is_command_enabled_for_user(spec: CommandSpec) -> bool:
    return meets_availability_requirement(spec) and resolve_enabled(spec)


@lru_cache
def built_in_command_specs() -> tuple[CommandSpec, ...]:
    """Static built-in slash commands for this batch migration."""
    from claude_code.commands.add_dir import ADD_DIR_COMMAND
    from claude_code.commands.additional_builtin_specs import ADDITIONAL_BUILTIN_COMMAND_SPECS
    from claude_code.commands.advisor import ADVISOR_COMMAND_SPEC
    from claude_code.commands.agents import AGENTS_COMMAND
    from claude_code.commands.branch import BRANCH_COMMAND
    from claude_code.commands.bridge import REMOTE_CONTROL_COMMAND
    from claude_code.commands.brief_command import BRIEF_COMMAND
    from claude_code.commands.btw import BTW_COMMAND
    from claude_code.commands.chrome import CHROME_COMMAND
    from claude_code.commands.clear import CLEAR_COMMAND
    from claude_code.commands.color import COLOR_COMMAND
    from claude_code.commands.compact import COMPACT_COMMAND
    from claude_code.commands.config import CONFIG_COMMAND
    from claude_code.commands.context import (
        CONTEXT_COMMAND,
        CONTEXT_NON_INTERACTIVE_COMMAND,
    )
    from claude_code.commands.copy import COPY_COMMAND
    from claude_code.commands.cost import COST_COMMAND
    from claude_code.commands.desktop import DESKTOP_COMMAND
    from claude_code.commands.diff import DIFF_COMMAND
    from claude_code.commands.doctor import DOCTOR_COMMAND
    from claude_code.commands.effort import EFFORT_COMMAND
    from claude_code.commands.exit import EXIT_COMMAND
    from claude_code.commands.export_command import EXPORT_COMMAND
    from claude_code.commands.extra_usage import (
        EXTRA_USAGE_COMMAND,
        EXTRA_USAGE_NON_INTERACTIVE_COMMAND,
    )
    from claude_code.commands.fast import FAST_COMMAND
    from claude_code.commands.feedback import FEEDBACK_COMMAND
    from claude_code.commands.files import FILES_COMMAND
    from claude_code.commands.heapdump import HEAPDUMP_COMMAND
    from claude_code.commands.help import HELP_COMMAND
    from claude_code.commands.mobile import MOBILE_COMMAND
    from claude_code.commands.privacy_settings import PRIVACY_SETTINGS_COMMAND
    from claude_code.commands.rate_limit_options import RATE_LIMIT_OPTIONS_COMMAND
    from claude_code.commands.release_notes import RELEASE_NOTES_COMMAND
    from claude_code.commands.reload_plugins import RELOAD_PLUGINS_COMMAND
    from claude_code.commands.rename import RENAME_COMMAND
    from claude_code.commands.rewind import REWIND_COMMAND
    from claude_code.commands.security_review import SECURITY_REVIEW_COMMAND_SPEC
    from claude_code.commands.session import SESSION_COMMAND
    from claude_code.commands.skills import SKILLS_COMMAND
    from claude_code.commands.stats import STATS_COMMAND
    from claude_code.commands.statusline import STATUSLINE_COMMAND
    from claude_code.commands.stickers import STICKERS_COMMAND
    from claude_code.commands.tag import TAG_COMMAND
    from claude_code.commands.tasks import TASKS_COMMAND
    from claude_code.commands.theme import THEME_COMMAND
    from claude_code.commands.thinkback import THINKBACK_COMMAND
    from claude_code.commands.thinkback_play import THINKBACK_PLAY_COMMAND
    from claude_code.commands.usage import USAGE_COMMAND

    return (
        ADD_DIR_COMMAND,
        ADVISOR_COMMAND_SPEC,
        AGENTS_COMMAND,
        BRANCH_COMMAND,
        BTW_COMMAND,
        CHROME_COMMAND,
        CLEAR_COMMAND,
        COLOR_COMMAND,
        COMPACT_COMMAND,
        CONFIG_COMMAND,
        CONTEXT_COMMAND,
        CONTEXT_NON_INTERACTIVE_COMMAND,
        COPY_COMMAND,
        COST_COMMAND,
        DESKTOP_COMMAND,
        DIFF_COMMAND,
        DOCTOR_COMMAND,
        EFFORT_COMMAND,
        EXIT_COMMAND,
        EXPORT_COMMAND,
        EXTRA_USAGE_COMMAND,
        EXTRA_USAGE_NON_INTERACTIVE_COMMAND,
        FAST_COMMAND,
        FEEDBACK_COMMAND,
        FILES_COMMAND,
        HEAPDUMP_COMMAND,
        HELP_COMMAND,
        PRIVACY_SETTINGS_COMMAND,
        RATE_LIMIT_OPTIONS_COMMAND,
        RELEASE_NOTES_COMMAND,
        RELOAD_PLUGINS_COMMAND,
        RENAME_COMMAND,
        REWIND_COMMAND,
        REMOTE_CONTROL_COMMAND,
        SECURITY_REVIEW_COMMAND_SPEC,
        SESSION_COMMAND,
        SKILLS_COMMAND,
        STATS_COMMAND,
        STATUSLINE_COMMAND,
        STICKERS_COMMAND,
        TAG_COMMAND,
        TASKS_COMMAND,
        THEME_COMMAND,
        THINKBACK_COMMAND,
        THINKBACK_PLAY_COMMAND,
        USAGE_COMMAND,
        BRIEF_COMMAND,
        MOBILE_COMMAND,
        *ADDITIONAL_BUILTIN_COMMAND_SPECS,
    )


def internal_only_specs() -> tuple[CommandSpec, ...]:
    """Subset matching INTERNAL_ONLY_COMMANDS from commands.ts for ant builds."""
    from claude_code.commands.bridge_kick import BRIDGE_KICK_SPEC
    from claude_code.commands.commit_command import COMMIT_COMMAND_SPEC
    from claude_code.commands.commit_push_pr import COMMIT_PUSH_PR_SPEC

    return (COMMIT_COMMAND_SPEC, COMMIT_PUSH_PR_SPEC, BRIDGE_KICK_SPEC)


def built_in_command_names() -> set[str]:
    names: set[str] = set()
    for spec in built_in_command_specs():
        names.add(spec.name)
        names.update(spec.aliases)
    return names


def find_command(command_name: str, commands: Iterable[CommandSpec]) -> CommandSpec | None:
    for spec in commands:
        if spec.name == command_name or command_name in spec.aliases:
            return spec
    return None


def has_command(command_name: str, commands: Iterable[CommandSpec]) -> bool:
    return find_command(command_name, commands) is not None


def get_command_or_raise(command_name: str, commands: list[CommandSpec]) -> CommandSpec:
    found = find_command(command_name, commands)
    if found is None:
        available = sorted(f"{s.name} ({', '.join(s.aliases)})" if s.aliases else s.name for s in commands)
        raise KeyError(f"Command {command_name} not found. Available: {', '.join(available)}")
    return found


def filter_visible(commands: Iterable[CommandSpec]) -> list[CommandSpec]:
    return [c for c in commands if is_command_enabled_for_user(c) and not resolve_hidden(c)]


def format_description_with_source(spec: CommandSpec) -> str:
    """User-facing description; mirrors formatDescriptionWithSource for builtins."""
    return resolve_description(spec)


def ant_internal_merged() -> list[CommandSpec]:
    base = list(built_in_command_specs())
    if os.environ.get("USER_TYPE") == "ant" and os.environ.get("IS_DEMO", "").lower() not in (
        "1",
        "true",
    ):
        base.extend(internal_only_specs())
    return base


__all__ = [
    "ant_internal_merged",
    "built_in_command_names",
    "built_in_command_specs",
    "filter_visible",
    "find_command",
    "format_description_with_source",
    "get_command_name",
    "get_command_or_raise",
    "has_command",
    "internal_only_specs",
    "is_command_enabled_for_user",
    "meets_availability_requirement",
]
