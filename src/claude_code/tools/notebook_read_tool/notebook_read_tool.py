"""
Read-only notebook inspection.

Python counterpart for NotebookRead (referenced in toolValidationConfig; no dedicated TS in leak).
"""

from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from ..base import Tool, ToolResult, ToolUseContext
from .constants import NOTEBOOK_READ_TOOL_NAME
from .prompt_text import DESCRIPTION, PROMPT


@dataclass
class NotebookReadInput:
    notebook_path: str
    max_preview_chars: int = 2000


@dataclass
class NotebookCellSummary:
    index: int
    cell_type: str
    source_preview: str


@dataclass
class NotebookReadOutput:
    path: str
    cells: list[NotebookCellSummary]


class NotebookReadTool(Tool[dict[str, Any], NotebookReadOutput]):
    @property
    def name(self) -> str:
        return NOTEBOOK_READ_TOOL_NAME

    @property
    def search_hint(self) -> str:
        return "read jupyter notebook cells"

    async def description(self) -> str:
        return DESCRIPTION

    async def prompt(self) -> str:
        return PROMPT

    def get_input_schema(self) -> dict[str, Any]:
        return {
            "type": "object",
            "properties": {
                "notebook_path": {"type": "string"},
                "max_preview_chars": {"type": "integer", "default": 2000},
            },
            "required": ["notebook_path"],
        }

    def get_output_schema(self) -> dict[str, Any]:
        return {
            "type": "object",
            "properties": {
                "path": {"type": "string"},
                "cells": {"type": "array"},
            },
        }

    async def execute(
        self,
        input: dict[str, Any],
        context: ToolUseContext,
    ) -> ToolResult:
        path = str(input.get("notebook_path", "")).strip()
        max_preview = int(input.get("max_preview_chars", 2000) or 2000)
        max_preview = max(100, min(max_preview, 50_000))

        if not path.endswith(".ipynb"):
            return ToolResult(success=False, error="Path must be a .ipynb file", error_code=1)

        p = Path(path).resolve()
        cwd = Path(context.get_cwd()).resolve()
        try:
            p.relative_to(cwd)
        except ValueError:
            return ToolResult(
                success=False,
                error="Notebook path must be under the current working directory",
                error_code=1,
            )

        if not p.is_file():
            return ToolResult(success=False, error=f"Not found: {p}", error_code=1)

        try:
            data = json.loads(p.read_text(encoding="utf-8", errors="replace"))
        except (OSError, json.JSONDecodeError) as e:
            return ToolResult(success=False, error=str(e), error_code=1)

        cells_raw = data.get("cells")
        if not isinstance(cells_raw, list):
            return ToolResult(success=False, error="Invalid notebook: missing cells array", error_code=1)

        summaries: list[NotebookCellSummary] = []
        for i, cell in enumerate(cells_raw):
            if not isinstance(cell, dict):
                continue
            ctype = str(cell.get("cell_type", "unknown"))
            src = cell.get("source", "")
            text = "".join(str(s) for s in src) if isinstance(src, list) else str(src)
            preview = text[:max_preview]
            if len(text) > max_preview:
                preview += "\n…"
            summaries.append(
                NotebookCellSummary(index=i, cell_type=ctype, source_preview=preview),
            )

        return ToolResult(
            success=True,
            output=NotebookReadOutput(path=str(p), cells=summaries),
        )
