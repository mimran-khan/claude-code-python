"""
List directory contents — fills gap where TS Read tool defers directories to shell.

TODO: Permission context, ignore rules (.gitignore), truncation policy.
"""

from __future__ import annotations

import asyncio
import os
from typing import Any

from ...utils.path_utils import expand_path
from ..base import Tool, ToolResult, ToolUseContext
from .constants import DESCRIPTION, LIST_DIR_TOOL_NAME
from .types import DirEntry, ListDirOutput


class ListDirTool(Tool[dict[str, Any], ListDirOutput]):
    @property
    def name(self) -> str:
        return LIST_DIR_TOOL_NAME

    @property
    def search_hint(self) -> str:
        return "list directory folder contents"

    async def description(self) -> str:
        return DESCRIPTION

    async def prompt(self) -> str:
        return DESCRIPTION

    def get_input_schema(self) -> dict[str, Any]:
        return {
            "type": "object",
            "properties": {
                "path": {
                    "type": "string",
                    "description": "Absolute directory path (defaults to cwd)",
                },
                "include_hidden": {"type": "boolean", "default": False},
            },
        }

    def get_output_schema(self) -> dict[str, Any]:
        return {
            "type": "object",
            "properties": {
                "directory": {"type": "string"},
                "entries": {"type": "array"},
            },
        }

    def get_path(self, input: dict[str, Any]) -> str | None:
        p = input.get("path")
        return expand_path(str(p)) if p else None

    async def check_permissions(
        self,
        input: dict[str, Any],
        context: ToolUseContext,
    ) -> dict[str, Any]:
        # TODO: checkReadPermissionForTool (TS)
        return {"behavior": "allow"}

    async def execute(
        self,
        input: dict[str, Any],
        context: ToolUseContext,
    ) -> ToolResult:
        raw = input.get("path")
        base = expand_path(str(raw)) if raw else context.get_cwd()
        include_hidden = bool(input.get("include_hidden", False))

        def _scan() -> ListDirOutput:
            if not os.path.isdir(base):
                raise NotADirectoryError(base)
            names = sorted(os.listdir(base))
            entries: list[DirEntry] = []
            for name in names:
                if not include_hidden and name.startswith("."):
                    continue
                full = os.path.join(base, name)
                try:
                    st = os.stat(full)
                    entries.append(
                        DirEntry(
                            name=name,
                            path=full,
                            is_directory=os.path.isdir(full),
                            size_bytes=None if os.path.isdir(full) else st.st_size,
                        )
                    )
                except OSError:
                    continue
            return ListDirOutput(directory=base, entries=entries)

        try:
            out = await asyncio.to_thread(_scan)
        except NotADirectoryError:
            return ToolResult(success=False, error=f"Not a directory: {base}", error_code=1)
        except OSError as e:
            return ToolResult(success=False, error=str(e), error_code=1)

        return ToolResult(success=True, output=out)
