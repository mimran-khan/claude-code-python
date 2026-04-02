"""
Bundled skill registry and on-disk extraction for reference files.

Migrated from: skills/bundledSkills.ts
"""

from __future__ import annotations

import os
import secrets
from collections import defaultdict
from collections.abc import Awaitable
from pathlib import Path

from ..utils.config_utils import get_claude_config_dir
from ..utils.debug import log_for_debugging
from .types import BundledSkillDefinition, GetPromptForCommand, PromptContentBlock, SkillCommand

_bundled_skills: list[SkillCommand] = []

_PROCESS_BUNDLED_NONCE = secrets.token_hex(8)


def get_bundled_skills_root() -> str:
    """Per-process directory for extracted bundled skill reference files."""
    root = os.path.join(
        get_claude_config_dir(),
        "tmp",
        "bundled-skills",
        _PROCESS_BUNDLED_NONCE,
    )
    os.makedirs(root, mode=0o700, exist_ok=True)
    return root


def get_bundled_skill_extract_dir(skill_name: str) -> str:
    return os.path.join(get_bundled_skills_root(), skill_name)


def _resolve_skill_file_path(base_dir: str, rel_path: str) -> str:
    normalized = os.path.normpath(rel_path.replace("/", os.sep))
    parts = normalized.split(os.sep)
    if os.path.isabs(normalized) or ".." in parts:
        msg = f"bundled skill file path escapes skill dir: {rel_path}"
        raise ValueError(msg)
    return os.path.join(base_dir, normalized)


def _write_skill_files(dir_path: str, files: dict[str, str]) -> None:
    by_parent: dict[str, list[tuple[str, str]]] = defaultdict(list)
    for rel_path, content in files.items():
        target = _resolve_skill_file_path(dir_path, rel_path)
        parent = str(Path(target).parent)
        by_parent[parent].append((target, content))

    for parent, entries in by_parent.items():
        Path(parent).mkdir(parents=True, mode=0o700, exist_ok=True)
        for target, content in entries:
            _safe_write_file(target, content)


def _safe_write_file(path: str, content: str) -> None:
    flags = os.O_WRONLY | os.O_CREAT | os.O_EXCL
    if hasattr(os, "O_NOFOLLOW"):
        flags |= os.O_NOFOLLOW
    fd = os.open(path, flags, 0o600)
    try:
        os.write(fd, content.encode("utf-8"))
    finally:
        os.close(fd)


async def _extract_bundled_skill_files(
    skill_name: str,
    files: dict[str, str],
) -> str | None:
    dir_path = get_bundled_skill_extract_dir(skill_name)
    try:
        _write_skill_files(dir_path, files)
        return dir_path
    except OSError as e:
        log_for_debugging(
            f"Failed to extract bundled skill '{skill_name}' to {dir_path}: {e}",
        )
        return None


def _prepend_base_dir(blocks: list[PromptContentBlock], base_dir: str) -> list[PromptContentBlock]:
    prefix = f"Base directory for this skill: {base_dir}\n\n"
    if blocks and blocks[0]["type"] == "text":
        first = blocks[0]["text"]
        return [{"type": "text", "text": prefix + first}, *blocks[1:]]
    return [{"type": "text", "text": prefix}, *blocks]


def register_bundled_skill(definition: BundledSkillDefinition) -> None:
    """Register a bundled skill (mirrors TS `registerBundledSkill`)."""
    files = definition.files
    skill_root: str | None = None
    get_prompt: GetPromptForCommand = definition.get_prompt_for_command

    if files:
        skill_root = get_bundled_skill_extract_dir(definition.name)
        promise_holder: dict[str, Awaitable[str | None] | None] = {"p": None}

        async def ensure_extract() -> str | None:
            if promise_holder["p"] is None:
                promise_holder["p"] = _extract_bundled_skill_files(definition.name, files)
            return await promise_holder["p"]

        inner = definition.get_prompt_for_command

        async def wrapped(args: str, ctx: object) -> list[PromptContentBlock]:
            extracted = await ensure_extract()
            blocks = await inner(args, ctx)  # type: ignore[arg-type]
            if extracted is None:
                return blocks
            return _prepend_base_dir(blocks, extracted)

        get_prompt = wrapped

    command = SkillCommand(
        type="prompt",
        name=definition.name,
        description=definition.description,
        aliases=definition.aliases,
        has_user_specified_description=True,
        allowed_tools=list(definition.allowed_tools or []),
        argument_hint=definition.argument_hint,
        when_to_use=definition.when_to_use,
        model=definition.model,
        disable_model_invocation=definition.disable_model_invocation,
        user_invocable=definition.user_invocable,
        content_length=0,
        source="bundled",
        loaded_from="bundled",
        hooks=definition.hooks,
        skill_root=skill_root,
        context=definition.context,
        agent=definition.agent,
        is_enabled=definition.is_enabled,
        is_hidden=not definition.user_invocable,
        progress_message="running",
        get_prompt_for_command=get_prompt,
    )
    _bundled_skills.append(command)


def get_bundled_skill_commands() -> list[SkillCommand]:
    return list(_bundled_skills)


def clear_bundled_skills() -> None:
    _bundled_skills.clear()


def get_bundled_skill_by_name(name: str) -> SkillCommand | None:
    for cmd in _bundled_skills:
        if cmd.name == name:
            return cmd
        if cmd.aliases and name in cmd.aliases:
            return cmd
    return None
