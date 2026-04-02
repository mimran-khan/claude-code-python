"""
Glob Tool — migrated from tools/GlobTool/GlobTool.ts.

Finds files under a directory using pathlib glob patterns with sensible default exclusions.
"""

from __future__ import annotations

import asyncio
import fnmatch
import os
import time
from pathlib import Path
from typing import Any

from ...utils.cwd import get_cwd
from ...utils.path_utils import expand_path
from ..base import Tool, ToolResult, ToolUseContext
from .constants import DESCRIPTION, GLOB_TOOL_NAME
from .types import GlobOutputModel

_DEFAULT_LIMIT = 100

_EXCLUDED_PATH_PARTS = frozenset(
    {
        ".git",
        ".svn",
        ".hg",
        ".bzr",
        "node_modules",
        "__pycache__",
        ".venv",
        "venv",
        ".tox",
        ".mypy_cache",
        ".idea",
        ".nox",
        "dist",
        "build",
        ".eggs",
    }
)


def _file_should_skip(path: Path, root: Path, extra_exclude_globs: list[str]) -> bool:
    try:
        resolved_root = root.resolve()
        rel = path.resolve().relative_to(resolved_root)
    except ValueError:
        return True
    if _EXCLUDED_PATH_PARTS.intersection(rel.parts):
        return True
    rel_posix = rel.as_posix()
    for pattern in extra_exclude_globs:
        p = pattern.strip()
        if not p:
            continue
        if fnmatch.fnmatch(rel_posix, p):
            return True
        if fnmatch.fnmatch(rel_posix.split("/")[-1], p):
            return True
    return False


def glob_tool_get_path(input: dict[str, Any]) -> str:
    p = input.get("path")
    if isinstance(p, str) and p.strip():
        return expand_path(p)
    return get_cwd()


class GlobTool(Tool[dict[str, Any], GlobOutputModel]):
    @property
    def name(self) -> str:
        return GLOB_TOOL_NAME

    @property
    def search_hint(self) -> str:
        return "find files by name pattern or wildcard"

    async def description(self) -> str:
        return DESCRIPTION

    async def prompt(self) -> str:
        return DESCRIPTION

    def get_input_schema(self) -> dict[str, Any]:
        return {
            "type": "object",
            "additionalProperties": False,
            "properties": {
                "pattern": {
                    "type": "string",
                    "description": "The glob pattern to match files against",
                },
                "path": {
                    "type": "string",
                    "description": "The directory to search in (optional; defaults to cwd)",
                },
            },
            "required": ["pattern"],
        }

    def get_output_schema(self) -> dict[str, Any]:
        return {
            "type": "object",
            "properties": {
                "durationMs": {"type": "number"},
                "numFiles": {"type": "integer"},
                "filenames": {"type": "array", "items": {"type": "string"}},
                "truncated": {"type": "boolean"},
            },
        }

    def get_path(self, input: dict[str, Any]) -> str | None:
        return glob_tool_get_path(input)

    async def validate_input(
        self,
        input: dict[str, Any],
        context: ToolUseContext,
    ) -> dict[str, Any]:
        p = input.get("path")
        if not p:
            return {"result": True}
        absolute = expand_path(str(p))
        if absolute.startswith("\\\\") or absolute.startswith("//"):
            return {"result": True}

        def _check() -> tuple[bool, str]:
            if not os.path.exists(absolute):
                return False, f"Directory does not exist: {p}"
            if not os.path.isdir(absolute):
                return False, f"Path is not a directory: {p}"
            return True, ""

        ok, msg = await asyncio.to_thread(_check)
        if not ok:
            code = 2 if "not a directory" in msg else 1
            return {"result": False, "message": msg, "errorCode": code}
        return {"result": True}

    async def check_permissions(
        self,
        input: dict[str, Any],
        context: ToolUseContext,
    ) -> dict[str, Any]:
        return {"behavior": "allow"}

    async def execute(
        self,
        input: dict[str, Any],
        context: ToolUseContext,
    ) -> ToolResult:
        return await glob_execute(input, context)


async def glob_execute(input: dict[str, Any], context: ToolUseContext) -> ToolResult:
    pattern = str(input.get("pattern", ""))
    if not pattern:
        return ToolResult(success=False, error="pattern is required", error_code=1)

    start = time.monotonic()
    base = glob_tool_get_path(input)
    limit = _DEFAULT_LIMIT
    gl = getattr(context, "glob_limits", None)
    if isinstance(gl, dict):
        mr = gl.get("maxResults")
        if isinstance(mr, int) and mr > 0:
            limit = min(mr, 50_000)

    raw_exclude = input.get("exclude")
    extra_exclude: list[str] = []
    if isinstance(raw_exclude, list):
        extra_exclude = [str(x) for x in raw_exclude if isinstance(x, str)]

    def _run() -> tuple[list[str], bool]:
        root = Path(base)
        if not root.is_dir():
            return [], False
        try:
            matches: list[Path] = []
            for path in root.glob(pattern):
                if not path.is_file():
                    continue
                if _file_should_skip(path, root, extra_exclude):
                    continue
                matches.append(path)
                if len(matches) >= limit + 1:
                    break
            truncated = len(matches) > limit
            files = matches[:limit]
            with_mtime = [(str(f), f.stat().st_mtime) for f in files]
            with_mtime.sort(key=lambda x: x[1], reverse=True)
            return [x[0] for x in with_mtime], truncated
        except (OSError, ValueError) as e:
            raise RuntimeError(str(e)) from e

    try:
        filenames, truncated = await asyncio.to_thread(_run)
    except RuntimeError as e:
        return ToolResult(success=False, error=str(e), error_code=1)

    out = GlobOutputModel(
        duration_ms=(time.monotonic() - start) * 1000,
        num_files=len(filenames),
        filenames=filenames,
        truncated=truncated,
    )
    return ToolResult(success=True, output=out)
