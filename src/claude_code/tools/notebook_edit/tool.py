"""
Notebook Edit Tool Implementation.

Edit Jupyter notebook cells.
"""

from __future__ import annotations

import json
import os
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Literal

from pydantic import BaseModel, Field

from ..base import Tool, ToolResult
from .prompt import DESCRIPTION, NOTEBOOK_EDIT_TOOL_NAME


class NotebookEditInput(BaseModel):
    """Input parameters for notebook edit tool."""

    notebook_path: str = Field(
        ...,
        description="Absolute path to the .ipynb file.",
    )
    cell_number: int = Field(
        ...,
        description="The 0-indexed cell number to edit.",
    )
    new_source: str = Field(
        default="",
        description="The new source content for the cell.",
    )
    edit_mode: Literal["replace", "insert", "delete"] = Field(
        default="replace",
        description="The edit mode: replace, insert, or delete.",
    )
    cell_type: Literal["code", "markdown", "raw"] = Field(
        default="code",
        description="The cell type for insert operations.",
    )


@dataclass
class NotebookEditSuccess:
    """Successful notebook edit result."""

    type: Literal["success"] = "success"
    notebook_path: str = ""
    cell_number: int = 0
    edit_mode: str = ""
    message: str = ""


@dataclass
class NotebookEditError:
    """Failed notebook edit result."""

    type: Literal["error"] = "error"
    notebook_path: str = ""
    error: str = ""


NotebookEditOutput = NotebookEditSuccess | NotebookEditError


class NotebookEditTool(Tool[NotebookEditInput, NotebookEditOutput]):
    """
    Tool for editing Jupyter notebook cells.

    Supports replacing, inserting, and deleting cells.
    """

    @property
    def name(self) -> str:
        return NOTEBOOK_EDIT_TOOL_NAME

    @property
    def description(self) -> str:
        return DESCRIPTION

    @property
    def input_schema(self) -> dict[str, Any]:
        return {
            "type": "object",
            "properties": {
                "notebook_path": {
                    "type": "string",
                    "description": "Absolute path to the .ipynb file.",
                },
                "cell_number": {
                    "type": "integer",
                    "description": "The 0-indexed cell number.",
                },
                "new_source": {
                    "type": "string",
                    "description": "The new source content for the cell.",
                },
                "edit_mode": {
                    "type": "string",
                    "enum": ["replace", "insert", "delete"],
                    "description": "The edit mode.",
                    "default": "replace",
                },
                "cell_type": {
                    "type": "string",
                    "enum": ["code", "markdown", "raw"],
                    "description": "The cell type for insert.",
                    "default": "code",
                },
            },
            "required": ["notebook_path", "cell_number"],
        }

    def is_read_only(self, input_data: NotebookEditInput) -> bool:
        return False

    def is_destructive(self, input_data: NotebookEditInput) -> bool:
        return input_data.edit_mode == "delete"

    async def call(
        self,
        input_data: NotebookEditInput,
        context: Any,
    ) -> ToolResult[NotebookEditOutput]:
        """Execute the notebook edit operation."""
        notebook_path = input_data.notebook_path
        cell_number = input_data.cell_number
        new_source = input_data.new_source
        edit_mode = input_data.edit_mode
        cell_type = input_data.cell_type

        # Validate path
        if not os.path.isabs(notebook_path):
            return ToolResult(
                success=False,
                output=NotebookEditError(
                    notebook_path=notebook_path,
                    error="Path must be absolute.",
                ),
            )

        path = Path(notebook_path)

        if not path.exists():
            return ToolResult(
                success=False,
                output=NotebookEditError(
                    notebook_path=notebook_path,
                    error=f"Notebook not found: {notebook_path}",
                ),
            )

        if path.suffix != ".ipynb":
            return ToolResult(
                success=False,
                output=NotebookEditError(
                    notebook_path=notebook_path,
                    error="File must be a .ipynb notebook.",
                ),
            )

        try:
            # Read notebook
            with open(path, encoding="utf-8") as f:
                notebook = json.load(f)

            cells = notebook.get("cells", [])

            # Validate cell number
            if edit_mode == "insert":
                if cell_number < 0 or cell_number > len(cells):
                    return ToolResult(
                        success=False,
                        output=NotebookEditError(
                            notebook_path=notebook_path,
                            error=f"Invalid cell number for insert: {cell_number}. Valid range: 0-{len(cells)}",
                        ),
                    )
            else:
                if cell_number < 0 or cell_number >= len(cells):
                    return ToolResult(
                        success=False,
                        output=NotebookEditError(
                            notebook_path=notebook_path,
                            error=f"Invalid cell number: {cell_number}. Valid range: 0-{len(cells) - 1}",
                        ),
                    )

            # Perform edit
            if edit_mode == "replace":
                cells[cell_number]["source"] = new_source.split("\n")
                message = f"Replaced cell {cell_number}"
            elif edit_mode == "insert":
                new_cell = {
                    "cell_type": cell_type,
                    "source": new_source.split("\n"),
                    "metadata": {},
                }
                if cell_type == "code":
                    new_cell["outputs"] = []
                    new_cell["execution_count"] = None
                cells.insert(cell_number, new_cell)
                message = f"Inserted new {cell_type} cell at {cell_number}"
            elif edit_mode == "delete":
                del cells[cell_number]
                message = f"Deleted cell {cell_number}"
            else:
                return ToolResult(
                    success=False,
                    output=NotebookEditError(
                        notebook_path=notebook_path,
                        error=f"Unknown edit mode: {edit_mode}",
                    ),
                )

            # Write notebook
            notebook["cells"] = cells
            with open(path, "w", encoding="utf-8") as f:
                json.dump(notebook, f, indent=1)

            return ToolResult(
                success=True,
                output=NotebookEditSuccess(
                    notebook_path=notebook_path,
                    cell_number=cell_number,
                    edit_mode=edit_mode,
                    message=message,
                ),
            )

        except json.JSONDecodeError as e:
            return ToolResult(
                success=False,
                output=NotebookEditError(
                    notebook_path=notebook_path,
                    error=f"Invalid notebook JSON: {e}",
                ),
            )
        except Exception as e:
            return ToolResult(
                success=False,
                output=NotebookEditError(
                    notebook_path=notebook_path,
                    error=str(e),
                ),
            )

    def user_facing_name(self, input_data: NotebookEditInput | None = None) -> str:
        """Get the user-facing name for this tool."""
        return "Notebook"

    def get_tool_use_summary(self, input_data: NotebookEditInput | None) -> str | None:
        """Get a short summary of this tool use."""
        if input_data:
            return f"{input_data.edit_mode} cell {input_data.cell_number}"
        return None
