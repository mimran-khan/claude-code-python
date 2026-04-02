"""
Load output style definitions from enabled plugins.

Migrated from: utils/plugins/loadPluginOutputStyles.ts
"""

from __future__ import annotations

import asyncio
import os
from dataclasses import dataclass
from typing import Literal

from ...types.plugin import get_plugin_error_message
from ..debug import log_for_debugging
from ..frontmatter import coerce_description_to_string, parse_frontmatter
from .plugin_loader import load_all_plugins_cache_only
from .walk_plugin_markdown import walk_plugin_markdown


@dataclass
class OutputStyleConfig:
    name: str
    description: str
    prompt: str
    source: Literal["plugin"] = "plugin"
    force_for_plugin: bool | None = None


_output_style_lock = asyncio.Lock()
_cached_styles: list[OutputStyleConfig] | None = None


def _is_duplicate_path(full_path: str, loaded: set[str]) -> bool:
    try:
        key = os.path.realpath(full_path)
    except OSError:
        key = full_path
    if key in loaded:
        return True
    loaded.add(key)
    return False


def _extract_description_from_markdown(content: str, fallback: str) -> str:
    for block in content.split("\n\n"):
        line = block.strip()
        if line and not line.startswith("#"):
            return line[:500]
    return fallback


async def _load_output_style_from_file(
    file_path: str,
    plugin_name: str,
    loaded_paths: set[str],
) -> OutputStyleConfig | None:
    if _is_duplicate_path(file_path, loaded_paths):
        return None
    try:

        def _read() -> OutputStyleConfig | None:
            with open(file_path, encoding="utf-8") as handle:
                content = handle.read()
            parsed = parse_frontmatter(content)
            fm = parsed.frontmatter
            base_name = os.path.splitext(os.path.basename(file_path))[0]
            name_fm = fm.extra.get("name") if fm.extra else None
            style_base = name_fm if isinstance(name_fm, str) else base_name
            style_name = f"{plugin_name}:{style_base}"
            desc = coerce_description_to_string(fm.description or "")
            if not desc.strip():
                desc = _extract_description_from_markdown(
                    parsed.content,
                    f"Output style from {plugin_name} plugin",
                )
            force_raw = fm.extra.get("force-for-plugin") if fm.extra else None
            if force_raw is True or force_raw == "true":
                force_for_plugin = True
            elif force_raw is False or force_raw == "false":
                force_for_plugin = False
            else:
                force_for_plugin = None
            return OutputStyleConfig(
                name=style_name,
                description=desc,
                prompt=parsed.content.strip(),
                force_for_plugin=force_for_plugin,
            )

        return await asyncio.to_thread(_read)
    except OSError as exc:
        log_for_debugging(
            f"Failed to load output style from {file_path}: {exc}",
            level="error",
        )
        return None


async def _load_output_styles_from_directory(
    output_styles_path: str,
    plugin_name: str,
    loaded_paths: set[str],
) -> list[OutputStyleConfig]:
    styles: list[OutputStyleConfig] = []

    async def on_file(full_path: str, _ns: list[str]) -> None:
        style = await _load_output_style_from_file(full_path, plugin_name, loaded_paths)
        if style:
            styles.append(style)

    await walk_plugin_markdown(
        output_styles_path,
        on_file,
        log_label="output-styles",
    )
    return styles


async def load_plugin_output_styles() -> list[OutputStyleConfig]:
    global _cached_styles
    async with _output_style_lock:
        if _cached_styles is not None:
            return list(_cached_styles)
        result = await load_all_plugins_cache_only()
        enabled = result.enabled
        errors = result.errors
        all_styles: list[OutputStyleConfig] = []

        if errors:
            log_for_debugging(
                "Plugin loading errors: " + ", ".join(get_plugin_error_message(e) for e in errors),
            )

        for plugin in enabled:
            loaded_paths: set[str] = set()
            if plugin.output_styles_path:
                try:
                    styles = await _load_output_styles_from_directory(
                        plugin.output_styles_path,
                        plugin.name,
                        loaded_paths,
                    )
                    all_styles.extend(styles)
                    if styles:
                        log_for_debugging(
                            f"Loaded {len(styles)} output styles from plugin {plugin.name} default directory",
                        )
                except OSError as exc:
                    log_for_debugging(
                        f"Failed to load output styles from plugin {plugin.name} default directory: {exc}",
                        level="error",
                    )

            extra_paths = plugin.output_styles_paths or []
            for style_path in extra_paths:
                try:
                    is_dir = await asyncio.to_thread(os.path.isdir, style_path)
                    if is_dir:
                        styles = await _load_output_styles_from_directory(
                            style_path,
                            plugin.name,
                            loaded_paths,
                        )
                        all_styles.extend(styles)
                        if styles:
                            log_for_debugging(
                                f"Loaded {len(styles)} output styles from plugin "
                                f"{plugin.name} custom path: {style_path}",
                            )
                    elif style_path.endswith(".md"):
                        style = await _load_output_style_from_file(
                            style_path,
                            plugin.name,
                            loaded_paths,
                        )
                        if style:
                            all_styles.append(style)
                            log_for_debugging(
                                f"Loaded output style from plugin {plugin.name} custom file: {style_path}",
                            )
                except OSError as exc:
                    log_for_debugging(
                        f"Failed to load output styles from plugin {plugin.name} custom path {style_path}: {exc}",
                        level="error",
                    )

        log_for_debugging(f"Total plugin output styles loaded: {len(all_styles)}")
        _cached_styles = all_styles
        return list(all_styles)


def clear_plugin_output_style_cache() -> None:
    global _cached_styles
    _cached_styles = None


__all__ = [
    "OutputStyleConfig",
    "clear_plugin_output_style_cache",
    "load_plugin_output_styles",
]
