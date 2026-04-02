"""
Migrated from: commands/init-verifiers.ts
"""

from __future__ import annotations

from dataclasses import dataclass

from ..base import Command, CommandContext, CommandResult
from .prompt import INIT_VERIFIERS_PROMPT


@dataclass(frozen=True)
class PromptContentBlock:
    """Mirrors API content block `{ type: 'text', text: ... }`."""

    type: str = "text"
    text: str = ""


@dataclass(frozen=True)
class InitVerifiersCommandMetadata:
    command_type: str = "prompt"
    name: str = "init-verifiers"
    description: str = "Create verifier skill(s) for automated verification of code changes"
    content_length: int = 0
    progress_message: str = "analyzing your project and creating verifier skills"
    source: str = "builtin"


init_verifiers_metadata = InitVerifiersCommandMetadata()


class InitVerifiersCommand(Command):
    @property
    def name(self) -> str:
        return init_verifiers_metadata.name

    @property
    def description(self) -> str:
        return init_verifiers_metadata.description

    @property
    def command_type(self):
        return "prompt"  # type: ignore[return-value]

    async def get_prompt_blocks(self) -> list[PromptContentBlock]:
        return [PromptContentBlock(text=INIT_VERIFIERS_PROMPT)]

    async def execute(self, context: CommandContext) -> CommandResult:
        blocks = await self.get_prompt_blocks()
        return CommandResult(
            success=True,
            output={"prompt_blocks": [b.__dict__ for b in blocks]},
        )
