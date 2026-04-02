"""Bundled /debug skill. Migrated from: skills/bundled/debug.ts"""

from __future__ import annotations

import os
from pathlib import Path

from ...bootstrap.state import get_session_id
from ...utils.debug import enable_debug_logging, get_debug_file_path
from ...utils.env_utils import get_claude_config_home_dir
from ...utils.errors import error_message, is_enoent
from ...utils.format import format_file_size
from ...utils.settings.settings import get_settings_file_path_for_source
from ..bundled_registry import register_bundled_skill
from ..types import BundledSkillDefinition

DEFAULT_DEBUG_LINES_READ = 20
TAIL_READ_BYTES = 64 * 1024
CLAUDE_CODE_GUIDE_AGENT_TYPE = "claude-code-guide"


def register_debug_skill() -> None:
    is_ant = os.environ.get("USER_TYPE") == "ant"
    description = (
        "Debug your current Claude Code session by reading the session debug log. Includes all event logging"
        if is_ant
        else "Enable debug logging for this session and help diagnose issues"
    )

    async def get_prompt_for_command(args: str, ctx: object) -> list[dict[str, str]]:
        del ctx
        was_already_logging = enable_debug_logging()
        debug_log_path = get_debug_file_path() or str(
            Path(get_claude_config_home_dir()) / "debug" / f"{get_session_id()}.log",
        )

        log_info: str
        try:
            p = debug_log_path
            if not p or not os.path.isfile(p):
                raise FileNotFoundError
            stats = os.stat(p)
            read_size = min(stats.st_size, TAIL_READ_BYTES)
            start_offset = max(0, stats.st_size - read_size)
            with open(p, "rb") as fh:
                fh.seek(start_offset)
                raw = fh.read(read_size)
            tail = raw.decode("utf-8", errors="replace").split("\n")[-DEFAULT_DEBUG_LINES_READ:]
            log_info = (
                f"Log size: {format_file_size(stats.st_size)}\n\n"
                f"### Last {DEFAULT_DEBUG_LINES_READ} lines\n\n```\n" + "\n".join(tail) + "\n```"
            )
        except OSError as e:
            log_info = (
                "No debug log exists yet — logging was just enabled."
                if is_enoent(e)
                else f"Failed to read last {DEFAULT_DEBUG_LINES_READ} lines of debug log: {error_message(e)}"
            )

        just_enabled_section = (
            ""
            if was_already_logging
            else f"""

## Debug Logging Just Enabled

Debug logging was OFF for this session until now. Nothing prior to this /debug invocation was captured.

Tell the user that debug logging is now active at `{debug_log_path}`, ask them to reproduce the issue, then re-read the log.
"""
        )

        user_path = get_settings_file_path_for_source("userSettings") or "(unknown)"
        project_path = get_settings_file_path_for_source("projectSettings") or "(unknown)"
        local_path = get_settings_file_path_for_source("localSettings") or "(unknown)"

        prompt = f"""# Debug Skill

Help the user debug an issue they're encountering in this current Claude Code session.
{just_enabled_section}
## Session Debug Log

The debug log for the current session is at: `{debug_log_path}`

{log_info}

For additional context, grep for [ERROR] and [WARN] lines across the full file.

## Issue Description

{args or "The user did not describe a specific issue. Read the debug log and summarize any errors, warnings, or notable issues."}

## Settings

Remember that settings are in:
* user - {user_path}
* project - {project_path}
* local - {local_path}

## Instructions

1. Review the user's issue description
2. The last {DEFAULT_DEBUG_LINES_READ} lines show the debug file format. Look for [ERROR] and [WARN] entries, stack traces, and failure patterns across the file
3. Consider launching the {CLAUDE_CODE_GUIDE_AGENT_TYPE} subagent to understand the relevant Claude Code features
4. Explain what you found in plain language
5. Suggest concrete fixes or next steps
"""
        return [{"type": "text", "text": prompt}]

    register_bundled_skill(
        BundledSkillDefinition(
            name="debug",
            description=description,
            allowed_tools=["Read", "Grep", "Glob"],
            argument_hint="[issue description]",
            disable_model_invocation=True,
            user_invocable=True,
            get_prompt_for_command=get_prompt_for_command,
        ),
    )
