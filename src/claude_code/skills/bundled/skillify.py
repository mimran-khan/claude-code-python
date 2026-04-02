"""Bundled /skillify skill. Migrated from: skills/bundled/skillify.ts"""

from __future__ import annotations

import os
from typing import Any

from ..bundled_registry import register_bundled_skill
from ..types import BundledSkillDefinition, ToolUseContext

SKILLIFY_TEMPLATE = """# Skillify {user_description_block}

You are capturing this session's repeatable process as a reusable skill.

## Your Session Context

Here is the session memory summary:
<session_memory>
{session_memory}
</session_memory>

Here are the user's messages during this session:
<user_messages>
{user_messages}
</user_messages>

## Your Task

Use AskUserQuestion to interview the user, then write a SKILL.md under `.claude/skills/<name>/SKILL.md`
or `~/.claude/skills/<name>/SKILL.md` per their choice.

Include frontmatter: name, description, allowed-tools, when_to_use, argument-hint, arguments, context.
"""


def _extract_user_text_from_messages(messages: list[Any]) -> list[str]:
    out: list[str] = []
    for m in messages:
        m_type = getattr(m, "type", None)
        if m_type != "user":
            continue
        msg = getattr(m, "message", m)
        content = getattr(msg, "content", "")
        if isinstance(content, str) and content.strip():
            out.append(content.strip())
            continue
        if isinstance(content, list):
            texts: list[str] = []
            for block in content:
                if isinstance(block, dict) and block.get("type") == "text":
                    texts.append(str(block.get("text", "")))
                elif hasattr(block, "type") and getattr(block, "type", None) == "text":
                    texts.append(str(getattr(block, "text", "")))
            joined = "\n".join(t for t in texts if t.strip()).strip()
            if joined:
                out.append(joined)
    return out


async def _session_memory_text() -> str:
    """Hook for session memory injection when `session_memory` service is wired."""
    return "No session memory available."


def register_skillify_skill() -> None:
    if os.environ.get("USER_TYPE") != "ant":
        return

    async def get_prompt_for_command(args: str, ctx: ToolUseContext) -> list[dict[str, str]]:
        session_memory = await _session_memory_text()
        try:
            from ...utils.messages import get_messages_after_compact_boundary

            raw_messages = getattr(ctx, "messages", []) or []
            msgs = get_messages_after_compact_boundary(raw_messages)
        except Exception:
            msgs = list(getattr(ctx, "messages", []) or [])
        user_messages = _extract_user_text_from_messages(msgs)
        user_block = f'The user described this process as: "{args}"' if args.strip() else ""
        prompt = (
            SKILLIFY_TEMPLATE.replace("{session_memory}", session_memory)
            .replace("{user_messages}", "\n\n---\n\n".join(user_messages) or "(none)")
            .replace("{user_description_block}", user_block)
        )
        return [{"type": "text", "text": prompt}]

    register_bundled_skill(
        BundledSkillDefinition(
            name="skillify",
            description=(
                "Capture this session's repeatable process into a skill. "
                "Call at end of the process you want to capture."
            ),
            allowed_tools=[
                "Read",
                "Write",
                "Edit",
                "Glob",
                "Grep",
                "AskUserQuestion",
                "Bash(mkdir:*)",
            ],
            user_invocable=True,
            disable_model_invocation=True,
            argument_hint="[description of the process you want to capture]",
            get_prompt_for_command=get_prompt_for_command,
        ),
    )
