"""
File Read Tool — migrated from tools/FileReadTool/FileReadTool.ts.

PDF/pages, token API, image resize pipeline, and host permission rules may be wired later.
"""

from __future__ import annotations

import asyncio
import base64
import json
import os
from pathlib import Path
from typing import Any

import aiofiles

from ...utils.file import detect_file_encoding
from ...utils.path_utils import expand_path
from ..base import Tool, ToolResult, ToolUseContext
from .constants import DESCRIPTION, FILE_READ_TOOL_NAME
from .limits import get_default_file_reading_limits
from .prompt_text import build_read_tool_prompt
from .read_formatting import add_line_numbers_from_lines
from .types import (
    FileReadImageResult,
    FileReadNotebookResult,
    FileReadTextResult,
    ImageDimensions,
    ImageFilePayload,
    NotebookFilePayload,
    TextFilePayload,
)

IMAGE_EXTENSIONS = frozenset({"png", "jpg", "jpeg", "gif", "webp"})

_BINARY_SNIFF_BYTES = 8_192


def _sample_looks_binary(data: bytes) -> bool:
    if not data:
        return False
    if b"\x00" in data:
        return True
    chunk = data[:_BINARY_SNIFF_BYTES]
    textish = sum(1 for b in chunk if b in (9, 10, 13) or 32 <= b < 127)
    return textish / max(len(chunk), 1) < 0.7


BLOCKED_DEVICE_PATHS = frozenset(
    {
        "/dev/zero",
        "/dev/random",
        "/dev/urandom",
        "/dev/full",
        "/dev/stdin",
        "/dev/tty",
        "/dev/console",
        "/dev/stdout",
        "/dev/stderr",
        "/dev/fd/0",
        "/dev/fd/1",
        "/dev/fd/2",
    }
)


class MaxFileReadTokenExceededError(Exception):
    def __init__(self, token_count: int, max_tokens: int) -> None:
        self.token_count = token_count
        self.max_tokens = max_tokens
        super().__init__(
            f"File content ({token_count} tokens) exceeds maximum allowed tokens ({max_tokens}). "
            "Use offset and limit parameters to read specific portions of the file."
        )


class FileReadTool(Tool[dict[str, Any], Any]):
    @property
    def name(self) -> str:
        return FILE_READ_TOOL_NAME

    @property
    def search_hint(self) -> str:
        return "read files, images, PDFs, notebooks"

    @property
    def max_result_size_chars(self) -> int:
        return 10**9

    @property
    def strict(self) -> bool:
        return True

    async def description(self) -> str:
        return DESCRIPTION

    async def prompt(self) -> str:
        lim = get_default_file_reading_limits()
        include = bool(lim.include_max_size_in_prompt) if lim.include_max_size_in_prompt is not None else False
        nudge = bool(lim.targeted_range_nudge) if lim.targeted_range_nudge is not None else False
        return build_read_tool_prompt(
            include_max_size_in_prompt=include,
            max_size_bytes=lim.max_size_bytes,
            targeted_range_nudge=nudge,
        )

    def get_input_schema(self) -> dict[str, Any]:
        return {
            "type": "object",
            "additionalProperties": False,
            "properties": {
                "file_path": {
                    "type": "string",
                    "description": "The absolute path to the file to read",
                },
                "offset": {
                    "type": "integer",
                    "description": "The line number to start reading from (1-based)",
                },
                "limit": {"type": "integer", "description": "The number of lines to read"},
                "encoding": {
                    "type": "string",
                    "description": "Text encoding (e.g. utf-8, latin-1). Default: detect from BOM / utf-8.",
                },
                "pages": {
                    "type": "string",
                    "description": 'Page range for PDF files (e.g. "1-5"). Not yet implemented in Python port.',
                },
            },
            "required": ["file_path"],
        }

    def get_output_schema(self) -> dict[str, Any]:
        return {
            "type": "object",
            "description": "Discriminated union type|text|image|notebook|pdf|file_unchanged",
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
        file_path = str(input.get("file_path", ""))
        if not file_path:
            return {"result": False, "message": "file_path is required", "errorCode": 1}
        if file_path in BLOCKED_DEVICE_PATHS:
            return {
                "result": False,
                "message": f"Cannot read from device path: {file_path}",
                "errorCode": 9,
            }
        pages = input.get("pages")
        if pages is not None and str(pages).strip():
            ext = Path(expand_path(file_path)).suffix.lower().lstrip(".")
            if ext != "pdf":
                return {
                    "result": False,
                    "message": "pages is only valid for .pdf files",
                    "errorCode": 7,
                }
        full = expand_path(file_path)
        if full.startswith("\\\\") or full.startswith("//"):
            return {"result": True}
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
        return await read_file(input, context)


async def read_file(input: dict[str, Any], context: ToolUseContext) -> ToolResult:
    file_path = str(input.get("file_path", ""))
    offset = input.get("offset")
    limit = input.get("limit")
    pages = input.get("pages")
    encoding_override = input.get("encoding")

    lim = get_default_file_reading_limits()
    full_path = expand_path(file_path)
    ext = Path(full_path).suffix.lower().lstrip(".")

    if pages is not None and str(pages).strip() and ext != "pdf":
        return ToolResult(
            success=False,
            error="pages parameter is only valid for PDF files",
            error_code=7,
        )

    if ext == "pdf":
        return ToolResult(
            success=False,
            error="PDF reading is not implemented in the Python port; convert or use another tool.",
            error_code=1,
        )

    if ext in IMAGE_EXTENSIONS:
        return await _read_image(full_path)

    if ext == "ipynb":
        return await _read_notebook(full_path, context, offset, limit)

    try:
        st = await asyncio.to_thread(os.stat, full_path)
        if st.st_size > lim.max_size_bytes:
            return ToolResult(
                success=False,
                error=f"File exceeds max read size ({lim.max_size_bytes} bytes)",
                error_code=1,
            )
    except FileNotFoundError:
        return ToolResult(success=False, error=f"File not found: {file_path}", error_code=1)
    except OSError as e:
        return ToolResult(success=False, error=str(e), error_code=1)

    enc = str(encoding_override).strip() if isinstance(encoding_override, str) else ""
    if not enc:
        enc = await asyncio.to_thread(detect_file_encoding, full_path)

    async with aiofiles.open(full_path, "rb") as rf:
        head = await rf.read(_BINARY_SNIFF_BYTES)
    if _sample_looks_binary(head):
        return ToolResult(
            success=False,
            error=(
                "File appears to be binary; read as text is not supported. "
                "Use a binary-capable workflow or specify a text file."
            ),
            error_code=8,
        )

    try:
        async with aiofiles.open(full_path, encoding=enc, errors="replace") as tf:
            text = await tf.read()
    except (OSError, UnicodeDecodeError) as e:
        return ToolResult(success=False, error=str(e), error_code=1)

    all_lines = text.splitlines(keepends=True)
    total_lines = len(all_lines)

    start_idx = 0
    if offset is not None:
        off = int(offset)
        start_idx = max(0, off - 1) if off > 0 else max(0, total_lines + off)

    end_idx = min(start_idx + int(limit), total_lines) if limit is not None else total_lines

    selected = all_lines[start_idx:end_idx]
    content = add_line_numbers_from_lines(selected, start_line=start_idx + 1)

    start_line_num = start_idx + 1
    payload = TextFilePayload(
        file_path=file_path,
        content=content,
        num_lines=len(selected),
        start_line=start_line_num,
        total_lines=total_lines,
    )
    out = FileReadTextResult(file=payload)

    context.read_file_state[full_path] = {
        "content": "".join(selected),
        "timestamp": float(int(os.path.getmtime(full_path) * 1000)),
        "offset": offset,
        "limit": limit,
        "is_partial_view": offset is not None or limit is not None,
    }

    return ToolResult(success=True, output=out)


async def _read_image(file_path: str) -> ToolResult:
    try:
        async with aiofiles.open(file_path, "rb") as f:
            raw = await f.read()
        size = len(raw)
    except OSError as e:
        return ToolResult(success=False, error=str(e), error_code=1)

    ext = Path(file_path).suffix.lower().lstrip(".")
    if ext in ("jpg", "jpeg"):
        mime = "image/jpeg"
    elif ext:
        mime = f"image/{ext}"
    else:
        mime = "image/png"
    b64 = base64.standard_b64encode(raw).decode("ascii")
    img = ImageFilePayload(
        base64=b64,
        media_type=mime,
        original_size=size,
        dimensions=ImageDimensions(),
    )
    return ToolResult(success=True, output=FileReadImageResult(file=img))


async def _read_notebook(
    file_path: str,
    context: ToolUseContext,
    offset: Any,
    limit: Any,
) -> ToolResult:
    try:
        async with aiofiles.open(file_path, encoding="utf-8", errors="replace") as f:
            raw_text = await f.read()
        data = json.loads(raw_text)
        cells_raw = data.get("cells", [])
        cells = cells_raw if isinstance(cells_raw, list) else []
    except (OSError, json.JSONDecodeError) as e:
        return ToolResult(success=False, error=str(e), error_code=1)
    nb = NotebookFilePayload(file_path=file_path, cells=cells)
    full_path = expand_path(file_path)
    context.read_file_state[full_path] = {
        "content": json.dumps(cells),
        "timestamp": float(int(os.path.getmtime(full_path) * 1000)),
        "offset": offset,
        "limit": limit,
        "is_partial_view": True,
    }
    return ToolResult(success=True, output=FileReadNotebookResult(file=nb))
