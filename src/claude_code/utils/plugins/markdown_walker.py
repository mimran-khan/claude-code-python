"""
Recursive markdown walk for plugin directories.

Migrated from: utils/plugins/walkPluginMarkdown.ts
"""

from __future__ import annotations

import logging
import os
import re
from collections.abc import Awaitable, Callable
from dataclasses import dataclass

from ..fs_operations import get_fs_implementation

logger = logging.getLogger(__name__)

SKILL_MD_RE = re.compile(r"^skill\.md$", re.IGNORECASE)


@dataclass
class WalkPluginMarkdownOptions:
    """Options for :func:`walk_plugin_markdown` (mirrors TS ``opts`` object)."""

    stop_at_skill_dir: bool = False
    log_label: str = "plugin"


async def walk_plugin_markdown(
    root_dir: str,
    on_file: Callable[[str, list[str]], Awaitable[None]],
    *,
    stop_at_skill_dir: bool = False,
    log_label: str = "plugin",
    options: WalkPluginMarkdownOptions | None = None,
) -> None:
    """
    Walk ``root_dir``, invoking ``on_file(full_path, namespace)`` for each ``.md`` file.

    When ``stop_at_skill_dir`` is True and a directory contains SKILL.md, only that
    directory's markdown files are visited (no deeper recursion).

    If ``options`` is set, it overrides ``stop_at_skill_dir`` and ``log_label``.
    """
    if options is not None:
        stop_at_skill_dir = options.stop_at_skill_dir
        log_label = options.log_label

    fs = get_fs_implementation()

    async def scan(dir_path: str, namespace: list[str]) -> None:
        try:
            entries = await fs.readdir(dir_path)
        except OSError as e:
            logger.error("Failed to scan %s directory %s: %s", log_label, dir_path, e)
            return

        if stop_at_skill_dir and any(e.is_file() and SKILL_MD_RE.match(e.name) for e in entries):
            await _emit_md_files(dir_path, entries, namespace)
            return

        for entry in entries:
            full_path = os.path.join(dir_path, entry.name)
            if entry.is_directory():
                await scan(full_path, [*namespace, entry.name])
            elif entry.is_file() and entry.name.lower().endswith(".md"):
                await on_file(full_path, namespace)

    async def _emit_md_files(
        dir_path: str,
        entries: list,
        namespace: list[str],
    ) -> None:
        for entry in entries:
            if entry.is_file() and entry.name.lower().endswith(".md"):
                await on_file(os.path.join(dir_path, entry.name), namespace)

    await scan(root_dir, [])


__all__ = ["WalkPluginMarkdownOptions", "walk_plugin_markdown"]
