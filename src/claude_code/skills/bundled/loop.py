"""Bundled /loop skill. Migrated from: skills/bundled/loop.ts"""

from __future__ import annotations

import os

from ...tools.schedule_cron.create import CRON_CREATE_TOOL_NAME, DEFAULT_MAX_AGE_DAYS
from ...tools.schedule_cron.delete import CRON_DELETE_TOOL_NAME
from ..bundled_registry import register_bundled_skill
from ..types import BundledSkillDefinition

DEFAULT_INTERVAL = "10m"

USAGE_MESSAGE = f"""Usage: /loop [interval] <prompt>

Run a prompt or slash command on a recurring interval.

Intervals: Ns, Nm, Nh, Nd (e.g. 5m, 30m, 2h, 1d). Minimum granularity is 1 minute.
If no interval is specified, defaults to {DEFAULT_INTERVAL}."""


def _is_kairos_cron_enabled() -> bool:
    return os.environ.get("CLAUDE_CODE_KAIROS_CRON", "").lower() in ("1", "true", "yes")


def _build_prompt(args: str) -> str:
    return f"""# /loop — schedule a recurring prompt

Parse the input into `[interval] <prompt…>` and schedule it with {CRON_CREATE_TOOL_NAME}.

## Parsing

1. Leading token matching `^\\d+[smhd]$` is the interval; rest is prompt.
2. Trailing `every <N><unit>` clause if present.
3. Default interval `{DEFAULT_INTERVAL}` if none.

## Action

1. Call {CRON_CREATE_TOOL_NAME} with cron, prompt, recurring true.
2. Confirm schedule; note auto-expire after {DEFAULT_MAX_AGE_DAYS} days; cancel with {CRON_DELETE_TOOL_NAME}.
3. Execute the parsed prompt immediately after scheduling.

## Input

{args}"""


def register_loop_skill() -> None:
    async def get_prompt_for_command(args: str, ctx: object) -> list[dict[str, str]]:
        del ctx
        trimmed = args.strip()
        if not trimmed:
            return [{"type": "text", "text": USAGE_MESSAGE}]
        return [{"type": "text", "text": _build_prompt(trimmed)}]

    register_bundled_skill(
        BundledSkillDefinition(
            name="loop",
            description=(
                "Run a prompt or slash command on a recurring interval "
                f"(e.g. /loop 5m /foo, defaults to {DEFAULT_INTERVAL})"
            ),
            when_to_use=(
                "When the user wants a recurring task or poll on an interval. Do NOT invoke for one-off tasks."
            ),
            argument_hint="[interval] <prompt>",
            user_invocable=True,
            is_enabled=_is_kairos_cron_enabled,
            get_prompt_for_command=get_prompt_for_command,
        ),
    )
