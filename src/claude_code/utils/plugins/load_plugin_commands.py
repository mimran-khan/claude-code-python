"""
Load slash commands from enabled plugins.

Migrated from: utils/plugins/loadPluginCommands.ts (simplified port).
"""

from __future__ import annotations

import asyncio
import os
from typing import Any

from ...bootstrap.state import get_session_id
from ...types.command import Command, PluginInfo, PromptCommand
from ...types.plugin import PluginManifest
from ..debug import log_for_debugging
from ..effort import EFFORT_LEVELS, parse_effort_value
from ..frontmatter import (
    coerce_description_to_string,
    parse_boolean_frontmatter,
    parse_frontmatter,
)
from ..model.model import parse_user_specified_model
from .plugin_loader import load_all_plugins_cache_only
from .plugin_options_storage import (
    load_plugin_options,
    substitute_plugin_variables,
    substitute_user_config_in_content,
)
from .walk_plugin_markdown import walk_plugin_markdown

_commands_lock = asyncio.Lock()
_cached_commands: list[Command] | None = None


def _extract_description_from_markdown(content: str, fallback: str) -> str:
    for block in content.split("\n\n"):
        line = block.strip()
        if line and not line.startswith("#"):
            return line[:500]
    return fallback


async def _collect_markdown_files(dir_path: str) -> list[tuple[str, str, Any, str]]:
    """Return list of (full_path, base_dir, frontmatter_dict, markdown_body)."""
    files: list[tuple[str, str, Any, str]] = []
    loaded: set[str] = set()

    async def on_file(full_path: str, _namespace: list[str]) -> None:
        try:
            key = os.path.realpath(full_path)
        except OSError:
            key = full_path
        if key in loaded:
            return
        loaded.add(key)

        def _read() -> None:
            with open(full_path, encoding="utf-8") as handle:
                raw = handle.read()
            parsed = parse_frontmatter(raw)
            files.append((full_path, dir_path, parsed.frontmatter, parsed.content))

        await asyncio.to_thread(_read)

    await walk_plugin_markdown(
        dir_path,
        on_file,
        stop_at_skill_dir=True,
        log_label="commands",
    )
    return files


def _command_name_from_file(file_path: str, base_dir: str, plugin_name: str) -> str:
    rel_dir = os.path.relpath(os.path.dirname(file_path), base_dir)
    base = os.path.splitext(os.path.basename(file_path))[0]
    if rel_dir in (".", ""):
        return f"{plugin_name}:{base}"
    ns = rel_dir.replace(os.sep, ":")
    return f"{plugin_name}:{ns}:{base}"


async def _build_plugin_command(
    command_name: str,
    file_path: str,
    plugin_manifest: PluginManifest,
    plugin_path: str,
    source_name: str,
    frontmatter: Any,
    markdown_content: str,
) -> Command | None:
    try:
        desc = coerce_description_to_string(frontmatter.description or "")
        if not desc.strip():
            desc = _extract_description_from_markdown(
                markdown_content,
                "Plugin command",
            )
        validated = coerce_description_to_string(frontmatter.description or "")
        has_user_desc = bool(str(validated).strip())

        allowed_raw = None
        if frontmatter.extra:
            allowed_raw = frontmatter.extra.get("allowed-tools")
        allowed_tools: list[str] | None = None
        if isinstance(allowed_raw, str):
            substituted = substitute_plugin_variables(
                allowed_raw,
                path=plugin_path,
                source=source_name,
            )
            allowed_tools = [s.strip() for s in substituted.split() if s.strip()]
        elif isinstance(allowed_raw, list):
            allowed_tools = []
            for item in allowed_raw:
                if isinstance(item, str):
                    allowed_tools.append(
                        substitute_plugin_variables(
                            item,
                            path=plugin_path,
                            source=source_name,
                        )
                    )

        arg_hint = (
            frontmatter.argument_hint
            if hasattr(frontmatter, "argument_hint")
            else frontmatter.extra.get("argument-hint")
            if frontmatter.extra
            else None
        )
        when_to_use = frontmatter.when_to_use
        version = frontmatter.version
        display_name = frontmatter.extra.get("name") if frontmatter.extra else None
        if not isinstance(display_name, str):
            display_name = None

        model_raw = frontmatter.model
        model = None
        if model_raw and model_raw != "inherit":
            model = parse_user_specified_model(str(model_raw))

        effort_raw = (
            frontmatter.effort
            if frontmatter.effort
            else (frontmatter.extra.get("effort") if frontmatter.extra else None)
        )
        effort = parse_effort_value(effort_raw) if effort_raw is not None else None
        if effort_raw is not None and effort is None:
            log_for_debugging(
                f"Plugin command {command_name} has invalid effort {effort_raw!r}. "
                f"Valid: {', '.join(EFFORT_LEVELS)} or an integer",
            )

        disable_mi = False
        if frontmatter.extra and "disable-model-invocation" in frontmatter.extra:
            disable_mi = bool(parse_boolean_frontmatter(str(frontmatter.extra["disable-model-invocation"])))

        user_invocable_val = frontmatter.extra.get("user-invocable") if frontmatter.extra else None
        if user_invocable_val is None:
            user_invocable = True
        else:
            parsed_ui = parse_boolean_frontmatter(str(user_invocable_val))
            user_invocable = True if parsed_ui is None else parsed_ui

        plugin_info = PluginInfo(
            plugin_manifest=plugin_manifest,
            repository=source_name,
        )

        async def get_prompt_for_command(_args: str, _context: Any) -> list[dict[str, Any]]:
            body = substitute_plugin_variables(
                markdown_content,
                path=plugin_path,
                source=source_name,
            )
            if plugin_manifest.user_config:
                body = substitute_user_config_in_content(
                    body,
                    load_plugin_options(source_name),
                    plugin_manifest.user_config,
                )
            sid = str(get_session_id())
            body = body.replace("${CLAUDE_SESSION_ID}", sid)
            return [{"type": "text", "text": body}]

        prompt = PromptCommand(
            progress_message="running",
            content_length=len(markdown_content),
            source="plugin",
            allowed_tools=allowed_tools,
            model=model,
            plugin_info=plugin_info,
            effort=effort,
            get_prompt_for_command=get_prompt_for_command,
        )

        return Command(
            name=command_name,
            description=desc,
            has_user_specified_description=has_user_desc,
            argument_hint=arg_hint if isinstance(arg_hint, str) else None,
            when_to_use=when_to_use,
            version=version,
            disable_model_invocation=disable_mi,
            user_invocable=user_invocable,
            is_hidden=not user_invocable,
            loaded_from="plugin",
            user_facing_name=(lambda dn=display_name, cn=command_name: dn or cn),
            prompt_command=prompt,
        )
    except Exception as exc:
        log_for_debugging(
            f"Failed to create command from {file_path}: {exc}",
            level="error",
        )
        return None


async def _load_commands_for_plugin(
    plugin: Any,
) -> list[Command]:
    out: list[Command] = []
    source_name = plugin.repository
    paths = []
    if plugin.commands_path:
        paths.append(plugin.commands_path)
    for extra in plugin.commands_paths or []:
        paths.append(extra)

    manifest = plugin.manifest
    if not isinstance(manifest, PluginManifest):
        return out

    for cmd_dir in paths:
        if not os.path.isdir(cmd_dir):
            continue
        files = await _collect_markdown_files(cmd_dir)
        for file_path, base_dir, fm, content in files:
            name = _command_name_from_file(file_path, base_dir, plugin.name)
            cmd = await _build_plugin_command(
                name,
                file_path,
                manifest,
                plugin.path,
                source_name,
                fm,
                content,
            )
            if cmd:
                out.append(cmd)
    return out


async def get_plugin_commands() -> list[Command]:
    global _cached_commands
    async with _commands_lock:
        if _cached_commands is not None:
            return list(_cached_commands)
        load = await load_all_plugins_cache_only()
        commands: list[Command] = []
        for plugin in load.enabled:
            commands.extend(await _load_commands_for_plugin(plugin))
        _cached_commands = commands
        return list(commands)


def clear_plugin_command_cache() -> None:
    global _cached_commands
    _cached_commands = None


__all__ = ["clear_plugin_command_cache", "get_plugin_commands"]
