"""
File Write Tool — migrated from tools/FileWriteTool/FileWriteTool.ts.

Host integrations (permissions, LSP, vscode notify, analytics) may be wired separately.
"""

from __future__ import annotations

import asyncio
import os
from pathlib import Path
from typing import Any

from ...utils.file import LineEndingType, get_file_modification_time, write_text_content_async
from ...utils.path_utils import expand_path
from ..base import Tool, ToolResult, ToolUseContext
from ..file_edit_tool.constants import FILE_UNEXPECTEDLY_MODIFIED_ERROR
from ..file_edit_tool.edit_utils import get_patch_for_edits
from ..file_edit_tool.types import FileEditRecord
from .constants import DESCRIPTION, FILE_WRITE_TOOL_NAME
from .prompt_text import get_write_tool_description
from .types import FileWriteOutputModel


class FileWriteTool(Tool[dict[str, Any], FileWriteOutputModel]):
    @property
    def name(self) -> str:
        return FILE_WRITE_TOOL_NAME

    @property
    def search_hint(self) -> str:
        return "create or overwrite files"

    @property
    def strict(self) -> bool:
        return True

    async def description(self) -> str:
        return DESCRIPTION

    async def prompt(self) -> str:
        return get_write_tool_description()

    def get_input_schema(self) -> dict[str, Any]:
        return {
            "type": "object",
            "additionalProperties": False,
            "properties": {
                "file_path": {
                    "type": "string",
                    "description": "The absolute path to the file to write (must be absolute, not relative)",
                },
                "content": {"type": "string", "description": "The content to write to the file"},
                "encoding": {
                    "type": "string",
                    "description": "Text encoding for the file (default utf-8)",
                },
                "line_endings": {
                    "type": "string",
                    "enum": ["LF", "CRLF"],
                    "description": "Line ending style (default LF)",
                },
            },
            "required": ["file_path", "content"],
        }

    def get_output_schema(self) -> dict[str, Any]:
        return {
            "type": "object",
            "properties": {
                "type": {"type": "string", "enum": ["create", "update"]},
                "filePath": {"type": "string"},
                "content": {"type": "string"},
                "structuredPatch": {"type": "array"},
                "originalFile": {"type": ["string", "null"]},
                "gitDiff": {"type": "object"},
            },
        }

    def get_path(self, input: dict[str, Any]) -> str | None:
        return input.get("file_path")

    def backfill_observable_input(self, input: dict[str, Any]) -> None:
        fp = input.get("file_path")
        if isinstance(fp, str):
            input["file_path"] = expand_path(fp)

    async def validate_input(
        self,
        input: dict[str, Any],
        context: ToolUseContext,
    ) -> dict[str, Any]:
        full = expand_path(str(input.get("file_path", "")))
        if full.startswith("\\\\") or full.startswith("//"):
            return {"result": True}
        try:
            await asyncio.to_thread(os.stat, full)
        except FileNotFoundError:
            return {"result": True}
        except OSError:
            raise

        rs = context.read_file_state.get(full)
        if not rs or rs.get("is_partial_view"):
            return {
                "result": False,
                "message": "File has not been read yet. Read it first before writing to it.",
                "errorCode": 2,
            }

        last_write = get_file_modification_time(full)
        prev_ts = float(rs.get("timestamp", rs.get("mtime_ms", 0)))
        if last_write > prev_ts:
            return {
                "result": False,
                "message": (
                    "File has been modified since read, either by the user or by a linter. "
                    "Read it again before attempting to write it."
                ),
                "errorCode": 3,
            }
        return {"result": True}

    async def check_permissions(
        self,
        input: dict[str, Any],
        context: ToolUseContext,
    ) -> dict[str, Any]:
        return {"behavior": "ask"}

    async def execute(
        self,
        input: dict[str, Any],
        context: ToolUseContext,
    ) -> ToolResult:
        return await write_file(input, context)


async def write_file(input: dict[str, Any], context: ToolUseContext) -> ToolResult:
    file_path = str(input.get("file_path", ""))
    content = str(input.get("content", ""))
    encoding = str(input.get("encoding") or "utf-8").strip() or "utf-8"
    le_raw = input.get("line_endings")
    line_endings: LineEndingType = "LF"
    if isinstance(le_raw, str) and le_raw.upper() == "CRLF":
        line_endings = "CRLF"

    full_path = expand_path(file_path)
    parent = str(Path(full_path).parent)
    if parent and parent != full_path:
        await asyncio.to_thread(os.makedirs, parent, exist_ok=True)

    def _read_old() -> str | None:
        try:
            with open(full_path, encoding="utf-8", errors="replace") as f:
                return f.read()
        except FileNotFoundError:
            return None

    old_content = await asyncio.to_thread(_read_old)
    file_exists = old_content is not None

    if file_exists:
        last_write = get_file_modification_time(full_path)
        last_read = context.read_file_state.get(full_path)
        lr_ts = float(last_read.get("timestamp", last_read.get("mtime_ms", 0))) if last_read else 0
        if not last_read or last_write > lr_ts:
            is_full = last_read and last_read.get("offset") is None and last_read.get("limit") is None
            unchanged = is_full and old_content == last_read.get("content") if last_read else False
            if not unchanged:
                return ToolResult(
                    success=False,
                    error=FILE_UNEXPECTEDLY_MODIFIED_ERROR,
                    error_code=3,
                )

    await write_text_content_async(
        full_path,
        content,
        encoding=encoding,
        line_endings=line_endings,
    )

    if file_exists and old_content is not None:
        try:
            patch, _ = get_patch_for_edits(
                full_path,
                old_content,
                [FileEditRecord(old_string=old_content, new_string=content, replace_all=False)],
            )
        except ValueError:
            patch = []
    else:
        patch = []

    context.read_file_state[full_path] = {
        "content": content,
        "timestamp": get_file_modification_time(full_path),
        "offset": None,
        "limit": None,
    }

    out = FileWriteOutputModel(
        type="update" if file_exists else "create",
        file_path=file_path,
        content=content,
        structured_patch=patch,
        original_file=old_content,
        git_diff=None,
    )
    return ToolResult(success=True, output=out)
