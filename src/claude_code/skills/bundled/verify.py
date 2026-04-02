"""Bundled /verify skill. Migrated from: skills/bundled/verify.ts"""

from __future__ import annotations

import os

import yaml

from ..bundled_registry import register_bundled_skill
from ..types import BundledSkillDefinition
from .verify_content import SKILL_FILES, SKILL_MD


def _description_from_skill_md() -> str:
    if not SKILL_MD.startswith("---"):
        return "Verify a code change does what it should by running the app."
    parts = SKILL_MD.split("---", 2)
    if len(parts) < 3:
        return "Verify a code change does what it should by running the app."
    try:
        fm = yaml.safe_load(parts[1]) or {}
    except yaml.YAMLError:
        return "Verify a code change does what it should by running the app."
    desc = fm.get("description")
    return str(desc) if isinstance(desc, str) else "Verify a code change does what it should by running the app."


def _skill_body_markdown() -> str:
    if SKILL_MD.startswith("---"):
        parts = SKILL_MD.split("---", 2)
        if len(parts) >= 3:
            return parts[2].strip()
    return SKILL_MD


def register_verify_skill() -> None:
    if os.environ.get("USER_TYPE") != "ant":
        return

    description = _description_from_skill_md()
    skill_body = _skill_body_markdown()

    async def get_prompt_for_command(args: str, ctx: object) -> list[dict[str, str]]:
        del ctx
        parts = [skill_body.lstrip()]
        if args.strip():
            parts.append(f"## User Request\n\n{args}")
        return [{"type": "text", "text": "\n\n".join(parts)}]

    register_bundled_skill(
        BundledSkillDefinition(
            name="verify",
            description=description,
            user_invocable=True,
            files=dict(SKILL_FILES),
            get_prompt_for_command=get_prompt_for_command,
        ),
    )
