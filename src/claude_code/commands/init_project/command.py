"""
Migrated from: commands/init.ts
"""

from __future__ import annotations

import os
from dataclasses import dataclass

from ..base import Command, CommandContext, CommandResult
from .prompts import NEW_INIT_PROMPT, OLD_INIT_PROMPT


def _is_env_truthy(value: str | None) -> bool:
    if value is None:
        return False
    return value.strip().lower() in ("1", "true", "yes", "on")


def _use_new_init_prompt() -> bool:
    """Parity: feature('NEW_INIT') && (USER_TYPE=='ant' || CLAUDE_CODE_NEW_INIT)."""

    new_init_flag = os.environ.get("CLAUDE_CODE_NEW_INIT")
    user_type = os.environ.get("USER_TYPE", "")
    new_init_bundle = os.environ.get("BUNDLE_NEW_INIT", "")
    if new_init_bundle and not _is_env_truthy(new_init_bundle):
        return False
    if not (new_init_bundle or os.environ.get("FEATURE_NEW_INIT")):
        return _is_env_truthy(new_init_flag) or user_type == "ant"
    return _is_env_truthy(os.environ.get("FEATURE_NEW_INIT", "")) and (
        user_type == "ant" or _is_env_truthy(new_init_flag)
    )


@dataclass(frozen=True)
class InitProjectMetadata:
    command_type: str = "prompt"
    name: str = "init"
    content_length: int = 0
    progress_message: str = "analyzing your codebase"
    source: str = "builtin"


init_project_metadata = InitProjectMetadata()


def init_description() -> str:
    if _use_new_init_prompt():
        return "Initialize new CLAUDE.md file(s) and optional skills/hooks with codebase documentation"
    return "Initialize a new CLAUDE.md file with codebase documentation"


class InitProjectCommand(Command):
    @property
    def name(self) -> str:
        return init_project_metadata.name

    @property
    def description(self) -> str:
        return init_description()

    @property
    def command_type(self):
        return "prompt"  # type: ignore[return-value]

    async def get_prompt_text(self) -> str:
        return NEW_INIT_PROMPT if _use_new_init_prompt() else OLD_INIT_PROMPT

    async def execute(self, context: CommandContext) -> CommandResult:
        text = await self.get_prompt_text()
        return CommandResult(
            success=True,
            output={
                "prompt_blocks": [{"type": "text", "text": text}],
                "maybe_mark_project_onboarding_complete": True,
            },
        )
