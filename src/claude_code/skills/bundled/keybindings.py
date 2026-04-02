"""Bundled keybindings-help skill. Migrated from: skills/bundled/keybindings.ts"""

from __future__ import annotations

import json
from typing import get_args

from ...keybindings.bindings import DEFAULT_BINDINGS
from ...keybindings.types import KeybindingContextName
from ..bundled_registry import register_bundled_skill
from ..types import BundledSkillDefinition


def _markdown_table(headers: list[str], rows: list[list[str]]) -> str:
    sep = ["---"] * len(headers)
    lines = [
        f"| {' | '.join(headers)} |",
        f"| {' | '.join(sep)} |",
        *[f"| {' | '.join(r)} |" for r in rows],
    ]
    return "\n".join(lines)


def _contexts_table() -> str:
    ctxs = list(get_args(KeybindingContextName))
    rows = [[f"`{c}`", "See Claude Code keybindings documentation"] for c in ctxs]
    return _markdown_table(["Context", "Description"], rows)


def _actions_table() -> str:
    rows: list[list[str]] = []
    for kb in DEFAULT_BINDINGS:
        rows.append([f"`{kb.action}`", kb.description or "—"])
    return _markdown_table(["Action", "Description"], rows)


def register_keybindings_skill() -> None:
    file_format_example = {
        "$schema": "https://www.schemastore.org/claude-code-keybindings.json",
        "bindings": [{"context": "Chat", "bindings": {"ctrl+e": "chat:externalEditor"}}],
    }

    section_intro = "\n".join(
        [
            "# Keybindings Skill",
            "",
            "Create or modify `~/.claude/keybindings.json` to customize keyboard shortcuts.",
            "",
            "## CRITICAL: Read Before Write",
            "",
            "Always read the existing file first; merge changes — never replace the entire file.",
        ],
    )

    async def get_prompt_for_command(args: str, ctx: object) -> list[dict[str, str]]:
        del ctx
        sections = [
            section_intro,
            "## File Format",
            "```json",
            json.dumps(file_format_example, indent=2),
            "```",
            "## Available Contexts",
            _contexts_table(),
            "## Default actions (subset)",
            _actions_table(),
            "## Validation",
            "Use `/doctor` or project validation to catch unknown contexts or bad keystrokes.",
        ]
        if args:
            sections.append(f"## User Request\n\n{args}")
        return [{"type": "text", "text": "\n\n".join(sections)}]

    register_bundled_skill(
        BundledSkillDefinition(
            name="keybindings-help",
            description=("Use when the user wants to customize keyboard shortcuts or modify keybindings.json."),
            allowed_tools=["Read"],
            user_invocable=False,
            is_enabled=lambda: True,
            get_prompt_for_command=get_prompt_for_command,
        ),
    )
