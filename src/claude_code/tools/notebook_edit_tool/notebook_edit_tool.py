"""
Notebook Edit Tool implementation.

Edit Jupyter notebooks.

Migrated from: tools/NotebookEditTool/NotebookEditTool.ts
"""

from __future__ import annotations

import json
import os
from dataclasses import dataclass
from typing import Any, Literal

from ..base import Tool, ToolResult, ToolUseContext

NOTEBOOK_EDIT_TOOL_NAME = "EditNotebook"


NOTEBOOK_EDIT_DESCRIPTION = """Edit a Jupyter notebook cell.

Use ONLY this tool to edit notebooks.

Supports:
- Editing existing cells
- Creating new cells
- Multiple cell types (python, markdown, etc.)
"""


NOTEBOOK_EDIT_PROMPT = """Edit a Jupyter notebook cell.

Important:
- Set is_new_cell correctly!
- Cell indices are 0-based
- old_string must be unique within the cell
"""


CellLanguage = Literal["python", "markdown", "javascript", "typescript", "r", "sql", "shell", "raw", "other"]


@dataclass
class NotebookEditInput:
    """Input for the Notebook Edit tool."""

    target_notebook: str
    cell_idx: int
    is_new_cell: bool
    cell_language: CellLanguage
    old_string: str
    new_string: str


class NotebookEditTool(Tool[dict[str, Any], dict[str, Any]]):
    """Tool for editing Jupyter notebooks."""

    @property
    def name(self) -> str:
        return NOTEBOOK_EDIT_TOOL_NAME

    @property
    def search_hint(self) -> str:
        return "edit notebook, jupyter cell"

    async def description(self) -> str:
        return NOTEBOOK_EDIT_DESCRIPTION

    async def prompt(self) -> str:
        return NOTEBOOK_EDIT_PROMPT

    def get_input_schema(self) -> dict[str, Any]:
        return {
            "type": "object",
            "properties": {
                "target_notebook": {
                    "type": "string",
                    "description": "Path to the notebook file",
                },
                "cell_idx": {
                    "type": "number",
                    "description": "Index of the cell (0-based)",
                },
                "is_new_cell": {
                    "type": "boolean",
                    "description": "True to create new cell, False to edit existing",
                },
                "cell_language": {
                    "type": "string",
                    "enum": [
                        "python",
                        "markdown",
                        "javascript",
                        "typescript",
                        "r",
                        "sql",
                        "shell",
                        "raw",
                        "other",
                    ],
                },
                "old_string": {
                    "type": "string",
                    "description": "Text to replace (empty for new cells)",
                },
                "new_string": {
                    "type": "string",
                    "description": "New text content",
                },
            },
            "required": [
                "target_notebook",
                "cell_idx",
                "is_new_cell",
                "cell_language",
                "old_string",
                "new_string",
            ],
        }

    def get_output_schema(self) -> dict[str, Any]:
        return {
            "type": "object",
            "properties": {
                "success": {"type": "boolean"},
                "cell_idx": {"type": "number"},
            },
        }

    def user_facing_name(self, input: dict[str, Any] | None = None) -> str:
        return NOTEBOOK_EDIT_TOOL_NAME

    def get_tool_use_summary(self, input: dict[str, Any] | None = None) -> str | None:
        if input and "target_notebook" in input:
            return input["target_notebook"]
        return None

    async def execute(
        self,
        input: dict[str, Any],
        context: ToolUseContext,
    ) -> ToolResult:
        """Execute the notebook edit."""
        notebook_path = input.get("target_notebook", "")
        cell_idx = input.get("cell_idx", 0)
        is_new_cell = input.get("is_new_cell", False)
        cell_language = input.get("cell_language", "python")
        old_string = input.get("old_string", "")
        new_string = input.get("new_string", "")

        # Expand path
        full_path = os.path.abspath(os.path.expanduser(notebook_path))

        try:
            if is_new_cell:
                return await self._create_cell(full_path, cell_idx, cell_language, new_string)
            else:
                return await self._edit_cell(full_path, cell_idx, old_string, new_string)
        except Exception as e:
            return ToolResult(
                success=False,
                error=str(e),
                error_code=1,
            )

    async def _create_cell(
        self,
        notebook_path: str,
        cell_idx: int,
        cell_language: str,
        content: str,
    ) -> ToolResult:
        """Create a new cell in the notebook."""
        # Read notebook
        with open(notebook_path) as f:
            notebook = json.load(f)

        # Determine cell type
        cell_type = "code" if cell_language not in ("markdown", "raw") else cell_language

        # Create new cell
        new_cell = {
            "cell_type": cell_type,
            "source": content.split("\n"),
            "metadata": {},
        }

        if cell_type == "code":
            new_cell["execution_count"] = None
            new_cell["outputs"] = []

        # Insert cell
        cells = notebook.get("cells", [])
        cells.insert(cell_idx, new_cell)
        notebook["cells"] = cells

        # Write notebook
        with open(notebook_path, "w") as f:
            json.dump(notebook, f, indent=2)

        return ToolResult(
            success=True,
            output={"cell_idx": cell_idx},
        )

    async def _edit_cell(
        self,
        notebook_path: str,
        cell_idx: int,
        old_string: str,
        new_string: str,
    ) -> ToolResult:
        """Edit an existing cell in the notebook."""
        # Read notebook
        with open(notebook_path) as f:
            notebook = json.load(f)

        cells = notebook.get("cells", [])

        if cell_idx < 0 or cell_idx >= len(cells):
            return ToolResult(
                success=False,
                error=f"Cell index {cell_idx} out of range",
                error_code=1,
            )

        cell = cells[cell_idx]
        source = cell.get("source", [])

        # Handle source as string or list
        content = "".join(source) if isinstance(source, list) else source

        # Check for old_string
        if old_string not in content:
            return ToolResult(
                success=False,
                error="old_string not found in cell",
                error_code=1,
            )

        # Replace
        new_content = content.replace(old_string, new_string, 1)
        cell["source"] = new_content.split("\n")

        # Write notebook
        with open(notebook_path, "w") as f:
            json.dump(notebook, f, indent=2)

        return ToolResult(
            success=True,
            output={"cell_idx": cell_idx},
        )
