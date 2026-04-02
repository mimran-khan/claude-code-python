"""
Load skills from ~/.claude/skills, managed policy dirs, project dirs, and legacy /commands.

Migrated from: skills/loadSkillsDir.ts (subset aligned with Python stack).
"""

from __future__ import annotations

import asyncio
import os
import re
from collections.abc import Callable
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Any, Literal, Protocol, cast

import yaml

from ..bootstrap.state import get_additional_directories_for_claude_md, get_session_id
from ..services.token_estimation import rough_token_count_estimation
from ..utils.config_utils import get_claude_config_dir
from ..utils.debug import log_for_debugging
from ..utils.env_utils import is_bare_mode, is_env_truthy
from ..utils.errors import is_enoent
from ..utils.git_ignore_rules import is_path_gitignored
from ..utils.settings.constants import SettingSource
from ..utils.settings.managed_path import get_managed_file_path
from .mcp_skill_builders import MCPSkillBuilders, register_mcp_skill_builders
from .types import (
    LoadedFrom,
    ParsedSkillFrontmatter,
    PromptContentBlock,
    SkillCommand,
    ToolUseContext,
)


def _log_event(_name: str, _payload: dict[str, Any]) -> None:
    try:
        from ..services.analytics.events import log_event as _le

        _le(_name, _payload)
    except Exception:
        pass


def is_setting_source_enabled(_source: SettingSource) -> bool:
    """Placeholder until merged settings gate is wired (TS: isSettingSourceEnabled)."""
    return True


def is_restricted_to_plugin_only(_kind: str) -> bool:
    """Placeholder (TS: isRestrictedToPluginOnly)."""
    return False


def get_skills_path(source: SettingSource | Literal["plugin"], dir_name: str) -> str:
    if source == "policySettings":
        return os.path.join(get_managed_file_path(), ".claude", dir_name)
    if source == "userSettings":
        return os.path.join(get_claude_config_dir(), dir_name)
    if source == "projectSettings":
        return os.path.join(".claude", dir_name)
    if source == "plugin":
        return "plugin"
    return ""


def estimate_skill_frontmatter_tokens(skill: SkillCommand) -> int:
    frontmatter_text = " ".join(x for x in (skill.name, skill.description, skill.when_to_use or "") if x)
    return rough_token_count_estimation(frontmatter_text)


def _parse_boolean_frontmatter(raw: Any) -> bool:
    if isinstance(raw, bool):
        return raw
    if raw is None:
        return False
    s = str(raw).strip().lower()
    return s in ("true", "1", "yes", "on")


def _coerce_description_to_string(raw: Any, _label: str) -> str | None:
    if raw is None:
        return None
    if isinstance(raw, str):
        return raw
    return str(raw)


def _extract_description_from_markdown(markdown: str, fallback_label: str) -> str:
    lines = markdown.strip().splitlines()
    buf: list[str] = []
    for line in lines:
        t = line.strip()
        if t.startswith("#"):
            continue
        if not t:
            if buf:
                break
            continue
        buf.append(t)
    if buf:
        return " ".join(buf)[:500]
    return f"{fallback_label} (no description)"


def _parse_allowed_tools(raw: Any) -> list[str]:
    if raw is None:
        return []
    if isinstance(raw, list):
        return [str(x) for x in raw]
    if isinstance(raw, str):
        parts = re.split(r"[\s,]+", raw.strip())
        return [p for p in parts if p]
    return []


def _parse_argument_names(raw: Any) -> list[str]:
    if raw is None:
        return []
    if isinstance(raw, list):
        return [str(x) for x in raw]
    if isinstance(raw, str):
        return [p.strip() for p in raw.split() if p.strip()]
    return []


def _split_paths_frontmatter(raw: Any) -> list[str]:
    if raw is None:
        return []
    items = [str(x).strip() for x in raw] if isinstance(raw, list) else re.split(r"[\n,]+", str(raw).strip())
    out: list[str] = []
    for p in items:
        p = p.strip()
        if not p:
            continue
        if p.endswith("/**"):
            p = p[:-3]
        out.append(p)
    if not out or all(x == "**" for x in out):
        return []
    return out


def _parse_hooks_from_frontmatter(
    frontmatter: dict[str, Any],
    skill_name: str,
) -> dict[str, Any] | None:
    hooks = frontmatter.get("hooks")
    if not hooks:
        return None
    if isinstance(hooks, dict):
        return hooks
    log_for_debugging(f"Invalid hooks in skill '{skill_name}': expected object")
    return None


def parse_skill_frontmatter_fields(
    frontmatter: dict[str, Any],
    markdown_content: str,
    resolved_name: str,
    description_fallback_label: Literal["Skill", "Custom command"] = "Skill",
) -> ParsedSkillFrontmatter:
    validated_description = _coerce_description_to_string(
        frontmatter.get("description"),
        resolved_name,
    )
    description = validated_description or _extract_description_from_markdown(
        markdown_content,
        description_fallback_label,
    )
    user_invocable = (
        True
        if frontmatter.get("user-invocable") is None
        else _parse_boolean_frontmatter(frontmatter.get("user-invocable"))
    )
    model_raw = frontmatter.get("model")
    model: str | None = None if model_raw == "inherit" or model_raw is None else str(model_raw)

    return ParsedSkillFrontmatter(
        display_name=str(frontmatter["name"]) if frontmatter.get("name") is not None else None,
        description=description,
        has_user_specified_description=validated_description is not None,
        allowed_tools=_parse_allowed_tools(frontmatter.get("allowed-tools")),
        argument_hint=str(frontmatter["argument-hint"]) if frontmatter.get("argument-hint") is not None else None,
        argument_names=_parse_argument_names(frontmatter.get("arguments")),
        when_to_use=str(frontmatter["when_to_use"]) if frontmatter.get("when_to_use") is not None else None,
        version=str(frontmatter["version"]) if frontmatter.get("version") is not None else None,
        model=model,
        disable_model_invocation=_parse_boolean_frontmatter(
            frontmatter.get("disable-model-invocation"),
        ),
        user_invocable=user_invocable,
        hooks=_parse_hooks_from_frontmatter(frontmatter, resolved_name),
        execution_context="fork" if frontmatter.get("context") == "fork" else None,
        agent=str(frontmatter["agent"]) if frontmatter.get("agent") is not None else None,
        effort=frontmatter.get("effort"),
        shell=frontmatter.get("shell"),
    )


def _substitute_arguments(
    content: str,
    args: str,
    argument_names: list[str],
) -> str:
    out = content.replace("$ARGUMENTS", args)
    parts = args.split() if args.strip() else []
    for i, p in enumerate(parts, start=1):
        out = out.replace(f"${i}", p)
    for i, name in enumerate(argument_names):
        token = f"${{{name}}}"
        if i < len(parts):
            out = out.replace(token, parts[i])
    return out


async def _maybe_execute_shell_in_prompt(
    content: str,
    _tool_use_context: ToolUseContext,
    _command_path: str,
    _shell: Any,
) -> str:
    """
    TS executes !` / ```! blocks here. Python port leaves content unchanged;
    wire `prompt_shell_execution` when available.
    """
    return content


def create_skill_command(
    *,
    skill_name: str,
    display_name: str | None,
    description: str,
    has_user_specified_description: bool,
    markdown_content: str,
    allowed_tools: list[str],
    argument_hint: str | None,
    argument_names: list[str],
    when_to_use: str | None,
    version: str | None,
    model: str | None,
    disable_model_invocation: bool,
    user_invocable: bool,
    source: str,
    base_dir: str | None,
    loaded_from: LoadedFrom,
    hooks: dict[str, Any] | None,
    execution_context: Literal["inline", "fork"] | None,
    agent: str | None,
    paths: list[str] | None,
    effort: Any,
    shell: Any,
) -> SkillCommand:
    effort_str: str | None = str(effort) if effort is not None else None

    async def get_prompt_for_command(
        args: str,
        tool_use_context: ToolUseContext,
    ) -> list[PromptContentBlock]:
        final_content = (
            f"Base directory for this skill: {base_dir}\n\n{markdown_content}" if base_dir else markdown_content
        )
        final_content = _substitute_arguments(final_content, args, argument_names)
        if base_dir:
            skill_dir = base_dir.replace("\\", "/") if os.name == "nt" else base_dir
            final_content = final_content.replace("${CLAUDE_SKILL_DIR}", skill_dir)
        final_content = final_content.replace("${CLAUDE_SESSION_ID}", str(get_session_id()))
        if loaded_from != "mcp":
            final_content = await _maybe_execute_shell_in_prompt(
                final_content,
                tool_use_context,
                f"/{skill_name}",
                shell,
            )
        return [{"type": "text", "text": final_content}]

    ctx: Literal["inline", "fork"] | None = execution_context
    return SkillCommand(
        type="prompt",
        name=skill_name,
        display_name=display_name,
        description=description,
        has_user_specified_description=has_user_specified_description,
        allowed_tools=allowed_tools,
        argument_hint=argument_hint,
        arg_names=argument_names if argument_names else None,
        when_to_use=when_to_use,
        version=version,
        model=model,
        disable_model_invocation=disable_model_invocation,
        user_invocable=user_invocable,
        context=ctx,
        agent=agent,
        effort=effort_str,
        paths=paths,
        content_length=len(markdown_content),
        is_hidden=not user_invocable,
        progress_message="running",
        source=cast(Any, source),
        loaded_from=loaded_from,
        hooks=hooks,
        skill_root=base_dir,
        get_prompt_for_command=get_prompt_for_command,
    )


@dataclass
class MarkdownFile:
    base_dir: str
    file_path: str
    frontmatter: dict[str, Any]
    content: str
    source: SettingSource


@dataclass
class SkillWithPath:
    skill: SkillCommand
    file_path: str


def _parse_frontmatter_file(raw: str, path: str) -> tuple[dict[str, Any], str]:
    if not raw.startswith("---"):
        return {}, raw
    parts = raw.split("---", 2)
    if len(parts) < 3:
        return {}, raw
    try:
        fm = yaml.safe_load(parts[1]) or {}
    except yaml.YAMLError:
        log_for_debugging(f"[skills] bad frontmatter YAML: {path}")
        return {}, parts[2].strip()
    if not isinstance(fm, dict):
        return {}, parts[2].strip()
    return fm, parts[2].strip()


async def _get_file_identity(file_path: str) -> str | None:
    try:
        return str(await asyncio.to_thread(lambda: Path(file_path).resolve()))
    except OSError:
        return None


def _is_skill_file(file_path: str) -> bool:
    return Path(file_path).name.lower() == "skill.md"


def _build_namespace(target_dir: str, base_dir: str) -> str:
    norm_base = base_dir.rstrip(os.sep)
    if os.path.abspath(target_dir) == os.path.abspath(norm_base):
        return ""
    rel = os.path.abspath(target_dir)[len(os.path.abspath(norm_base)) :].lstrip(os.sep)
    return rel.replace(os.sep, ":") if rel else ""


def _skill_command_name(file_path: str, base_dir: str) -> str:
    skill_dir = str(Path(file_path).parent)
    parent_of_skill = str(Path(skill_dir).parent)
    command_base = Path(skill_dir).name
    ns = _build_namespace(parent_of_skill, base_dir)
    return f"{ns}:{command_base}" if ns else command_base


def _regular_command_name(file_path: str, base_dir: str) -> str:
    file_directory = str(Path(file_path).parent)
    file_name = Path(file_path).stem
    ns = _build_namespace(file_directory, base_dir)
    return f"{ns}:{file_name}" if ns else file_name


def _command_name_for_markdown(file: MarkdownFile) -> str:
    if _is_skill_file(file.file_path):
        return _skill_command_name(file.file_path, file.base_dir)
    return _regular_command_name(file.file_path, file.base_dir)


def transform_skill_files(files: list[MarkdownFile]) -> list[MarkdownFile]:
    by_dir: dict[str, list[MarkdownFile]] = {}
    for f in files:
        d = str(Path(f.file_path).parent)
        by_dir.setdefault(d, []).append(f)
    out: list[MarkdownFile] = []
    for _d, dir_files in by_dir.items():
        skills = [f for f in dir_files if _is_skill_file(f.file_path)]
        if skills:
            out.append(skills[0])
            if len(skills) > 1:
                log_for_debugging(
                    f"Multiple skill files in {_d}, using {Path(skills[0].file_path).name}",
                )
        else:
            out.extend(dir_files)
    return out


async def load_skills_from_skills_dir(base_path: str, source: SettingSource) -> list[SkillWithPath]:
    results: list[SkillWithPath] = []
    try:
        entries = await asyncio.to_thread(os.listdir, base_path)
    except OSError as e:
        if not is_enoent(e):
            log_for_debugging(f"[skills] readdir {base_path}: {e}")
        return []

    async def one(entry: str) -> SkillWithPath | None:
        skill_dir_path = os.path.join(base_path, entry)
        is_dir = await asyncio.to_thread(os.path.isdir, skill_dir_path)
        is_link = await asyncio.to_thread(os.path.islink, skill_dir_path)
        if not (is_dir or is_link):
            return None
        skill_file_path = os.path.join(skill_dir_path, "SKILL.md")
        try:
            raw = await asyncio.to_thread(
                lambda: Path(skill_file_path).read_text(encoding="utf-8"),
            )
        except OSError as e:
            if not is_enoent(e):
                log_for_debugging(f"[skills] failed to read {skill_file_path}: {e}")
            return None
        fm, body = _parse_frontmatter_file(raw, skill_file_path)
        skill_name = entry
        parsed = parse_skill_frontmatter_fields(fm, body, skill_name)
        paths = _split_paths_frontmatter(fm.get("paths"))
        cmd = create_skill_command(
            **asdict(parsed),
            skill_name=skill_name,
            markdown_content=body,
            source=source,
            base_dir=skill_dir_path,
            loaded_from="skills",
            paths=paths,
        )
        return SkillWithPath(skill=cmd, file_path=skill_file_path)

    for entry in entries:
        sp = await one(entry)
        if sp:
            results.append(sp)
    return results


async def _walk_command_markdown(commands_root: str, source: SettingSource) -> list[MarkdownFile]:
    out: list[MarkdownFile] = []
    root = Path(commands_root)
    if not root.is_dir():
        return out

    def walk() -> None:
        for p in root.rglob("*.md"):
            try:
                raw = p.read_text(encoding="utf-8")
            except OSError:
                continue
            fm, body = _parse_frontmatter_file(raw, str(p))
            out.append(
                MarkdownFile(
                    base_dir=str(root),
                    file_path=str(p),
                    frontmatter=fm,
                    content=body,
                    source=source,
                ),
            )

    await asyncio.to_thread(walk)
    return out


async def load_skills_from_commands_dir(cwd: str) -> list[SkillWithPath]:
    commands_dir = os.path.join(cwd, ".claude", "commands")
    try:
        files = await _walk_command_markdown(commands_dir, "projectSettings")
        processed = transform_skill_files(files)
        skills: list[SkillWithPath] = []
        for mf in processed:
            try:
                is_skill_fmt = _is_skill_file(mf.file_path)
                skill_directory = str(Path(mf.file_path).parent) if is_skill_fmt else None
                cmd_name = _command_name_for_markdown(mf)
                parsed = parse_skill_frontmatter_fields(
                    mf.frontmatter,
                    mf.content,
                    cmd_name,
                    "Custom command",
                )
                cmd = create_skill_command(
                    **asdict(parsed),
                    skill_name=cmd_name,
                    display_name=None,
                    markdown_content=mf.content,
                    source=mf.source,
                    base_dir=skill_directory,
                    loaded_from="commands_DEPRECATED",
                    paths=None,
                )
                skills.append(SkillWithPath(skill=cmd, file_path=mf.file_path))
            except Exception as e:  # noqa: BLE001
                log_for_debugging(f"[skills] commands dir parse error: {e}")
        return skills
    except Exception as e:  # noqa: BLE001
        log_for_debugging(f"[skills] load commands: {e}")
        return []


def get_project_dirs_up_to_home(subdir: str, cwd: str) -> list[str]:
    paths: list[str] = []
    cur = os.path.abspath(cwd)
    home = os.path.abspath(os.path.expanduser("~"))
    while True:
        candidate = os.path.join(cur, ".claude", subdir)
        if os.path.isdir(candidate):
            paths.append(candidate)
        if cur == home:
            break
        parent = os.path.dirname(cur)
        if parent == cur:
            break
        cur = parent
    return paths


_SKILL_DIR_CACHE: dict[str, list[SkillCommand]] = {}
_conditional_skills: dict[str, SkillCommand] = {}
_activated_conditional: set[str] = set()
_dynamic_skill_dirs: set[str] = set()
_dynamic_skills: dict[str, SkillCommand] = {}
_dynamic_listeners: list[Callable[[], None]] = []


class OnSkillsLoaded(Protocol):
    def __call__(self) -> None: ...


def on_dynamic_skills_loaded(callback: Callable[[], None]) -> Callable[[], None]:
    _dynamic_listeners.append(callback)

    def unsub() -> None:
        if callback in _dynamic_listeners:
            _dynamic_listeners.remove(callback)

    return unsub


def _emit_skills_loaded() -> None:
    for cb in list(_dynamic_listeners):
        try:
            cb()
        except Exception as e:  # noqa: BLE001
            log_for_debugging(f"[skills] listener error: {e}")


async def _load_skill_dir_commands_impl(cwd: str) -> list[SkillCommand]:
    user_skills_dir = os.path.join(get_claude_config_dir(), "skills")
    managed_skills_dir = os.path.join(get_managed_file_path(), ".claude", "skills")
    project_skills_dirs = get_project_dirs_up_to_home("skills", cwd)
    additional_dirs = get_additional_directories_for_claude_md()
    skills_locked = is_restricted_to_plugin_only("skills")
    project_settings_enabled = is_setting_source_enabled("projectSettings") and not skills_locked

    if is_bare_mode():
        if not additional_dirs or not project_settings_enabled:
            return []
        nested = await asyncio.gather(
            *[
                load_skills_from_skills_dir(
                    os.path.join(d, ".claude", "skills"),
                    "projectSettings",
                )
                for d in additional_dirs
            ],
        )
        return [s.skill for batch in nested for s in batch]

    async def load_managed() -> list[SkillWithPath]:
        if is_env_truthy(os.environ.get("CLAUDE_CODE_DISABLE_POLICY_SKILLS")):
            return []
        return await load_skills_from_skills_dir(managed_skills_dir, "policySettings")

    async def load_user() -> list[SkillWithPath]:
        if is_setting_source_enabled("userSettings") and not skills_locked:
            return await load_skills_from_skills_dir(user_skills_dir, "userSettings")
        return []

    async def load_project() -> list[list[SkillWithPath]]:
        if not project_settings_enabled or not project_skills_dirs:
            return []
        return list(
            await asyncio.gather(
                *[load_skills_from_skills_dir(d, "projectSettings") for d in project_skills_dirs],
            ),
        )

    async def load_additional() -> list[list[SkillWithPath]]:
        if not project_settings_enabled or not additional_dirs:
            return []
        return list(
            await asyncio.gather(
                *[
                    load_skills_from_skills_dir(
                        os.path.join(d, ".claude", "skills"),
                        "projectSettings",
                    )
                    for d in additional_dirs
                ],
            ),
        )

    async def load_legacy() -> list[SkillWithPath]:
        if skills_locked:
            return []
        return await load_skills_from_commands_dir(cwd)

    (
        managed_skills,
        user_skills,
        project_skills_flat,
        additional_flat,
        legacy_cmds,
    ) = await asyncio.gather(
        load_managed(),
        load_user(),
        load_project(),
        load_additional(),
        load_legacy(),
    )

    all_with_paths: list[SkillWithPath] = [
        *managed_skills,
        *user_skills,
        *[s for batch in project_skills_flat for s in batch],
        *[s for batch in additional_flat for s in batch],
        *legacy_cmds,
    ]

    identities = await asyncio.gather(
        *[_get_file_identity(sp.file_path) for sp in all_with_paths],
    )
    seen: dict[str, str] = {}
    deduped: list[SkillCommand] = []
    for sp, fid in zip(all_with_paths, identities, strict=True):
        if fid is None:
            deduped.append(sp.skill)
            continue
        prev = seen.get(fid)
        if prev is not None:
            log_for_debugging(
                f"Skipping duplicate skill '{sp.skill.name}' from {sp.skill.source} "
                f"(same file already loaded from {prev})",
            )
            continue
        seen[fid] = str(sp.skill.source)
        deduped.append(sp.skill)

    unconditional: list[SkillCommand] = []
    new_conditional: list[SkillCommand] = []
    for skill in deduped:
        if skill.paths and len(skill.paths) > 0 and skill.name not in _activated_conditional:
            new_conditional.append(skill)
        else:
            unconditional.append(skill)
    for s in new_conditional:
        _conditional_skills[s.name] = s
    return unconditional


async def get_skill_dir_commands(cwd: str) -> list[SkillCommand]:
    if cwd in _SKILL_DIR_CACHE:
        return _SKILL_DIR_CACHE[cwd]
    loaded = await _load_skill_dir_commands_impl(cwd)
    _SKILL_DIR_CACHE[cwd] = loaded
    return loaded


def clear_skill_caches() -> None:
    _SKILL_DIR_CACHE.clear()
    _conditional_skills.clear()
    _activated_conditional.clear()


get_command_dir_commands = get_skill_dir_commands
clear_command_caches = clear_skill_caches


def _path_matches_conditional(rel_path: str, pattern: str) -> bool:
    rel_path = rel_path.replace("\\", "/").strip("/")
    pat = pattern.strip().replace("\\", "/").rstrip("/")
    if pat == "**":
        return True
    if "**" in pat:
        rx = "^" + re.escape(pat).replace(r"\*\*", ".*").replace(r"\*", "[^/]*") + "$"
        return re.match(rx, rel_path) is not None
    return fnmatch_path(rel_path, pat)


def fnmatch_path(path: str, pattern: str) -> bool:
    import fnmatch

    return fnmatch.fnmatch(path, pattern) or path == pattern.rstrip("/")


def activate_conditional_skills_for_paths(file_paths: list[str], cwd: str) -> list[str]:
    if not _conditional_skills:
        return []
    cwd_abs = os.path.abspath(cwd)
    activated: list[str] = []
    for name, skill in list(_conditional_skills.items()):
        if not skill.paths:
            continue
        for fp in file_paths:
            rel = os.path.relpath(fp, cwd_abs) if os.path.isabs(fp) else fp
            rel = rel.replace("\\", "/")
            if not rel or rel.startswith("..") or os.path.isabs(rel):
                continue
            if any(_path_matches_conditional(rel, p) for p in skill.paths):
                _dynamic_skills[name] = skill
                del _conditional_skills[name]
                _activated_conditional.add(name)
                activated.append(name)
                log_for_debugging(
                    f"[skills] Activated conditional skill '{name}' (matched path: {rel})",
                )
                break
    if activated:
        _log_event(
            "tengu_dynamic_skills_changed",
            {
                "source": "conditional_paths",
                "addedCount": len(activated),
            },
        )
        _emit_skills_loaded()
    return activated


async def discover_skill_dirs_for_paths(file_paths: list[str], cwd: str) -> list[str]:
    resolved_cwd = cwd.rstrip(os.sep)
    new_dirs: list[str] = []
    for fp in file_paths:
        current = str(Path(fp).parent)
        while current.startswith(resolved_cwd + os.sep):
            skill_dir = os.path.join(current, ".claude", "skills")
            if skill_dir not in _dynamic_skill_dirs:
                _dynamic_skill_dirs.add(skill_dir)
                if await asyncio.to_thread(os.path.isdir, skill_dir):
                    if await is_path_gitignored(current, resolved_cwd):
                        log_for_debugging(f"[skills] Skipped gitignored skills dir: {skill_dir}")
                    else:
                        new_dirs.append(skill_dir)
            parent = str(Path(current).parent)
            if parent == current:
                break
            current = parent
    new_dirs.sort(key=lambda p: p.count(os.sep), reverse=True)
    return new_dirs


async def add_skill_directories(dirs: list[str]) -> None:
    if not is_setting_source_enabled("projectSettings") or is_restricted_to_plugin_only(
        "skills",
    ):
        return
    if not dirs:
        return
    prev = set(_dynamic_skills.keys())
    loaded = await asyncio.gather(
        *[load_skills_from_skills_dir(d, "projectSettings") for d in dirs],
    )
    for batch in reversed(loaded):
        for sp in batch:
            _dynamic_skills[sp.skill.name] = sp.skill
    added = [n for n in _dynamic_skills if n not in prev]
    if added:
        _log_event(
            "tengu_dynamic_skills_changed",
            {"source": "file_operation", "addedCount": len(added)},
        )
    _emit_skills_loaded()


def get_dynamic_skills() -> list[SkillCommand]:
    return list(_dynamic_skills.values())


def get_conditional_skill_count() -> int:
    return len(_conditional_skills)


def clear_dynamic_skills() -> None:
    _dynamic_skill_dirs.clear()
    _dynamic_skills.clear()
    _conditional_skills.clear()
    _activated_conditional.clear()


register_mcp_skill_builders(
    MCPSkillBuilders(
        create_skill_command=create_skill_command,
        parse_skill_frontmatter_fields=parse_skill_frontmatter_fields,
    ),
)
