"""
Grep Tool — migrated from tools/GrepTool/GrepTool.ts.

Uses ripgrep (`rg`) when available; falls back to a Python regex walk with similar filters.
"""

from __future__ import annotations

import asyncio
import contextlib
import os
import shutil
from typing import Any

from ...utils.cwd import get_cwd
from ...utils.path_utils import expand_path
from ..base import Tool, ToolResult, ToolUseContext
from .constants import GREP_TOOL_NAME, get_description
from .types import GrepOutputModel

_DEFAULT_HEAD_LIMIT = 250
_RG_TIMEOUT_SEC = 120.0
_MAX_RAW_STDOUT_BYTES = 4 * 1024 * 1024

_DEFAULT_RG_GLOB_EXCLUDES = (
    "!.git/**",
    "!.svn/**",
    "!.hg/**",
    "!.bzr/**",
    "!**/node_modules/**",
    "!**/__pycache__/**",
    "!**/.venv/**",
    "!**/venv/**",
    "!**/.mypy_cache/**",
    "!**/.tox/**",
    "!**/dist/**",
    "!**/build/**",
)


def grep_get_path(input: dict[str, Any]) -> str:
    p = input.get("path")
    if isinstance(p, str) and p.strip():
        return expand_path(p)
    return get_cwd()


class GrepTool(Tool[dict[str, Any], GrepOutputModel]):
    @property
    def name(self) -> str:
        return GREP_TOOL_NAME

    @property
    def search_hint(self) -> str:
        return "search file contents with regex (ripgrep)"

    @property
    def strict(self) -> bool:
        return True

    @property
    def max_result_size_chars(self) -> int:
        return 20_000

    async def description(self) -> str:
        return get_description()

    async def prompt(self) -> str:
        return get_description()

    def user_facing_name(self, input: dict[str, Any] | None = None) -> str:
        return "Search"

    def get_input_schema(self) -> dict[str, Any]:
        return {
            "type": "object",
            "additionalProperties": False,
            "properties": {
                "pattern": {"type": "string"},
                "path": {"type": "string"},
                "glob": {"type": "string"},
                "output_mode": {
                    "type": "string",
                    "enum": ["content", "files_with_matches", "count"],
                },
                "-B": {"type": "integer"},
                "-A": {"type": "integer"},
                "-C": {"type": "integer"},
                "context": {"type": "integer"},
                "-n": {"type": "boolean"},
                "-i": {"type": "boolean"},
                "type": {"type": "string"},
                "head_limit": {"type": "integer"},
                "offset": {"type": "integer"},
                "multiline": {"type": "boolean"},
            },
            "required": ["pattern"],
        }

    def get_output_schema(self) -> dict[str, Any]:
        return {"type": "object"}

    def get_path(self, input: dict[str, Any]) -> str | None:
        return grep_get_path(input)

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

        def _exists() -> bool:
            return os.path.exists(absolute)

        if not await asyncio.to_thread(_exists):
            return {
                "result": False,
                "message": f"Path does not exist: {p}",
                "errorCode": 1,
            }
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
        return await grep_execute(input, context)


async def grep_execute(input: dict[str, Any], _context: ToolUseContext) -> ToolResult:
    pattern = str(input.get("pattern", ""))
    if not pattern:
        return ToolResult(success=False, error="pattern is required", error_code=1)

    search_path = grep_get_path(input)
    output_mode = str(input.get("output_mode", "files_with_matches"))
    case_insensitive = bool(input.get("-i", False))
    glob_pat = input.get("glob")
    file_type = input.get("type")
    head_limit = input.get("head_limit")
    offset = int(input.get("offset") or 0)
    multiline = bool(input.get("multiline", False))
    show_line_numbers = bool(input.get("-n", True))
    ctx_before = input.get("-B")
    ctx_after = input.get("-A")
    ctx_both = input.get("-C") or input.get("context")

    rg = shutil.which("rg")
    if not rg:
        return await _python_grep_fallback(
            pattern,
            search_path or ".",
            output_mode,
            case_insensitive,
            glob_pat,
            head_limit,
            offset,
        )

    cmd: list[str] = [rg, "--hidden", "--max-columns", "500"]
    if multiline:
        cmd.extend(["-U", "--multiline-dotall"])
    if case_insensitive:
        cmd.append("-i")
    if output_mode == "files_with_matches":
        cmd.append("-l")
    elif output_mode == "count":
        cmd.append("-c")
    if output_mode == "content" and show_line_numbers:
        cmd.append("-n")
    if output_mode == "content" and ctx_both is not None:
        cmd.extend(["-C", str(int(ctx_both))])
    elif output_mode == "content":
        if ctx_before is not None:
            cmd.extend(["-B", str(int(ctx_before))])
        if ctx_after is not None:
            cmd.extend(["-A", str(int(ctx_after))])

    for d in (".git", ".svn", ".hg", ".bzr"):
        cmd.extend(["--glob", f"!{d}"])
    for gex in _DEFAULT_RG_GLOB_EXCLUDES:
        cmd.extend(["--glob", gex])

    if pattern.startswith("-"):
        cmd.extend(["-e", pattern])
    else:
        cmd.append(pattern)

    if file_type:
        cmd.extend(["--type", str(file_type)])

    if glob_pat:
        for part in str(glob_pat).split():
            cmd.extend(["--glob", part])

    cmd.append(search_path or ".")

    proc = await asyncio.create_subprocess_exec(
        *cmd,
        stdout=asyncio.subprocess.PIPE,
        stderr=asyncio.subprocess.PIPE,
    )
    try:
        stdout_b, stderr_b = await asyncio.wait_for(proc.communicate(), timeout=_RG_TIMEOUT_SEC)
    except TimeoutError:
        proc.kill()
        with contextlib.suppress(OSError):
            await proc.wait()
        return ToolResult(
            success=False,
            error=f"ripgrep timed out after {_RG_TIMEOUT_SEC:.0f}s",
            error_code=1,
        )

    output_truncated = len(stdout_b) > _MAX_RAW_STDOUT_BYTES
    if output_truncated:
        stdout_b = stdout_b[:_MAX_RAW_STDOUT_BYTES]

    text = stdout_b.decode("utf-8", errors="replace")
    if proc.returncode not in (0, 1):
        err = stderr_b.decode("utf-8", errors="replace")
        return ToolResult(
            success=False,
            error=err or f"ripgrep exited with {proc.returncode}",
            error_code=1,
        )

    lines = [ln for ln in text.splitlines() if ln]
    eff_limit = None if head_limit == 0 else (int(head_limit) if head_limit is not None else _DEFAULT_HEAD_LIMIT)
    if eff_limit is not None:
        sliced = lines[offset : offset + eff_limit]
        truncated = len(lines) - offset > eff_limit
        applied_limit = eff_limit if truncated else None
        lines = sliced
    else:
        lines = lines[offset:]
        applied_limit = None

    applied_offset = offset if offset > 0 else None

    if output_mode == "content":
        body = "\n".join(lines)
        warn = stderr_b.decode("utf-8", errors="replace").strip() or None
        return ToolResult(
            success=True,
            output=GrepOutputModel(
                mode="content",
                num_files=0,
                filenames=[],
                content=body,
                num_lines=len(lines),
                applied_limit=applied_limit,
                applied_offset=applied_offset,
                output_truncated=output_truncated,
                stderr=warn,
            ),
        )

    if output_mode == "count":
        total = 0
        file_count = 0
        for ln in lines:
            if ":" in ln:
                _, _, rest = ln.rpartition(":")
                try:
                    total += int(rest.strip())
                    file_count += 1
                except ValueError:
                    continue
        warn = stderr_b.decode("utf-8", errors="replace").strip() or None
        return ToolResult(
            success=True,
            output=GrepOutputModel(
                mode="count",
                num_files=file_count,
                filenames=[],
                content="\n".join(lines),
                num_matches=total,
                applied_limit=applied_limit,
                applied_offset=applied_offset,
                output_truncated=output_truncated,
                stderr=warn,
            ),
        )

    warn = stderr_b.decode("utf-8", errors="replace").strip() or None
    return ToolResult(
        success=True,
        output=GrepOutputModel(
            mode="files_with_matches",
            num_files=len(lines),
            filenames=lines,
            applied_limit=applied_limit,
            applied_offset=applied_offset,
            output_truncated=output_truncated,
            stderr=warn,
        ),
    )


async def _python_grep_fallback(
    pattern: str,
    search_path: str,
    output_mode: str,
    case_insensitive: bool,
    glob_pat: Any,
    head_limit: Any,
    offset: int,
) -> ToolResult:
    import fnmatch
    import re

    try:
        flags = re.IGNORECASE if case_insensitive else 0
        rx = re.compile(pattern, flags)
    except re.error as e:
        return ToolResult(success=False, error=f"Invalid regex: {e}", error_code=1)

    if not os.path.exists(search_path):
        return ToolResult(
            success=False,
            error=f"Path not found: {search_path}",
            error_code=1,
        )

    eff_limit = None if head_limit == 0 else (int(head_limit) if head_limit is not None else _DEFAULT_HEAD_LIMIT)
    matches: list[str] = []
    files_seen: set[str] = set()
    per_file_match_counts: dict[str, int] = {}

    def walk() -> None:
        for root, dirs, files in os.walk(search_path):
            dirs[:] = [d for d in dirs if not d.startswith(".") and d not in {"node_modules", "__pycache__", ".git"}]
            for fname in files:
                if glob_pat and not fnmatch.fnmatch(fname, str(glob_pat)):
                    continue
                fp = os.path.join(root, fname)
                try:
                    with open(fp, encoding="utf-8", errors="replace") as f:
                        for i, line in enumerate(f, 1):
                            if rx.search(line):
                                if output_mode == "files_with_matches":
                                    files_seen.add(fp)
                                    break
                                if output_mode == "count":
                                    per_file_match_counts[fp] = per_file_match_counts.get(fp, 0) + 1
                                else:
                                    matches.append(f"{fp}:{i}:{line.rstrip()}")
                except OSError:
                    continue

    await asyncio.to_thread(walk)

    if output_mode == "files_with_matches":
        names = sorted(files_seen)
        slice_names = names[offset:] if eff_limit is None else names[offset : offset + eff_limit]
        return ToolResult(
            success=True,
            output=GrepOutputModel(
                mode="files_with_matches",
                num_files=len(slice_names),
                filenames=slice_names,
                applied_limit=eff_limit if eff_limit and len(names) - offset > eff_limit else None,
                applied_offset=offset if offset else None,
            ),
        )

    if output_mode == "count":
        total_matches = sum(per_file_match_counts.values())
        return ToolResult(
            success=True,
            output=GrepOutputModel(
                mode="count",
                num_files=len(per_file_match_counts),
                filenames=[],
                content=None,
                num_lines=None,
                num_matches=total_matches,
                applied_limit=None,
                applied_offset=None,
            ),
        )

    slice_matches = matches[offset:] if eff_limit is None else matches[offset : offset + eff_limit]
    return ToolResult(
        success=True,
        output=GrepOutputModel(
            mode="content",
            num_files=0,
            filenames=[],
            content="\n".join(slice_matches),
            num_lines=len(slice_matches),
            applied_limit=eff_limit if eff_limit and len(matches) - offset > eff_limit else None,
            applied_offset=offset if offset else None,
        ),
    )
