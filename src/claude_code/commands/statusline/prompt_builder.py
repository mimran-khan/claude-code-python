"""Migrated from: commands/statusline.tsx (getPromptForCommand)."""

from __future__ import annotations

from dataclasses import dataclass

AGENT_TOOL_NAME = "Agent"


@dataclass(frozen=True)
class PromptTextBlock:
    type: str = "text"
    text: str = ""


async def build_statusline_prompt(args: str) -> list[PromptTextBlock]:
    prompt = args.strip() or "Configure my statusLine from my shell PS1 configuration"
    return [
        PromptTextBlock(
            text=(f'Create an {AGENT_TOOL_NAME} with subagent_type "statusline-setup" and the prompt "{prompt}"'),
        ),
    ]


__all__ = ["AGENT_TOOL_NAME", "PromptTextBlock", "build_statusline_prompt"]
