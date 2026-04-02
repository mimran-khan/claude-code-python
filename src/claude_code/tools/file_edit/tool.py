"""
File Edit Tool Implementation.

Performs exact string replacements in files.
"""

from __future__ import annotations

import os
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Literal

from pydantic import BaseModel, Field

from ..base import Tool, ToolResult
from .prompt import FILE_EDIT_TOOL_NAME, get_edit_tool_description


class FileEditInput(BaseModel):
    """Input parameters for file edit tool."""

    path: str = Field(
        ...,
        description="The absolute path to the file to modify.",
    )
    old_string: str = Field(
        ...,
        description="The text to replace.",
    )
    new_string: str = Field(
        ...,
        description="The text to replace it with (must be different from old_string).",
    )
    replace_all: bool = Field(
        default=False,
        description="Replace all occurrences of old_string (default false).",
    )


@dataclass
class FileEditSuccess:
    """Successful file edit result."""

    type: Literal["success"] = "success"
    file_path: str = ""
    replacements_made: int = 1
    message: str = ""


@dataclass
class FileEditError:
    """Failed file edit result."""

    type: Literal["error"] = "error"
    file_path: str = ""
    error: str = ""


FileEditOutput = FileEditSuccess | FileEditError


class FileEditTool(Tool[FileEditInput, FileEditOutput]):
    """
    Tool for performing exact string replacements in files.

    Supports single or multiple replacements via the replace_all flag.
    """

    @property
    def name(self) -> str:
        return FILE_EDIT_TOOL_NAME

    @property
    def description(self) -> str:
        return get_edit_tool_description()

    @property
    def input_schema(self) -> dict[str, Any]:
        return {
            "type": "object",
            "properties": {
                "path": {
                    "type": "string",
                    "description": "The absolute path to the file to modify.",
                },
                "old_string": {
                    "type": "string",
                    "description": "The text to replace.",
                },
                "new_string": {
                    "type": "string",
                    "description": "The text to replace it with (must be different from old_string).",
                },
                "replace_all": {
                    "type": "boolean",
                    "description": "Replace all occurrences of old_string (default false).",
                    "default": False,
                },
            },
            "required": ["path", "old_string", "new_string"],
        }

    def is_read_only(self, input_data: FileEditInput) -> bool:
        return False

    def is_destructive(self, input_data: FileEditInput) -> bool:
        return True

    async def call(
        self,
        input_data: FileEditInput,
        context: Any,
    ) -> ToolResult[FileEditOutput]:
        """Execute the file edit operation."""
        file_path = input_data.path
        old_string = input_data.old_string
        new_string = input_data.new_string
        replace_all = input_data.replace_all

        # Validate path is absolute
        if not os.path.isabs(file_path):
            return ToolResult(
                success=False,
                output=FileEditError(
                    file_path=file_path,
                    error="Path must be absolute.",
                ),
            )

        path = Path(file_path)

        # Check file exists
        if not path.exists():
            return ToolResult(
                success=False,
                output=FileEditError(
                    file_path=file_path,
                    error=f"File not found: {file_path}",
                ),
            )

        # Check it's a file
        if not path.is_file():
            return ToolResult(
                success=False,
                output=FileEditError(
                    file_path=file_path,
                    error=f"Not a file: {file_path}",
                ),
            )

        # Validate old_string != new_string
        if old_string == new_string:
            return ToolResult(
                success=False,
                output=FileEditError(
                    file_path=file_path,
                    error="old_string and new_string must be different.",
                ),
            )

        try:
            # Read current content
            content = path.read_text(encoding="utf-8")

            # Count occurrences
            count = content.count(old_string)

            if count == 0:
                return ToolResult(
                    success=False,
                    output=FileEditError(
                        file_path=file_path,
                        error="old_string not found in file. Make sure it matches exactly, including whitespace and indentation.",
                    ),
                )

            if count > 1 and not replace_all:
                return ToolResult(
                    success=False,
                    output=FileEditError(
                        file_path=file_path,
                        error=f"old_string appears {count} times in the file. Use replace_all=true to replace all occurrences, or provide more context to make old_string unique.",
                    ),
                )

            # Perform replacement
            if replace_all:
                new_content = content.replace(old_string, new_string)
                replacements = count
            else:
                new_content = content.replace(old_string, new_string, 1)
                replacements = 1

            # Write back
            path.write_text(new_content, encoding="utf-8")

            return ToolResult(
                success=True,
                output=FileEditSuccess(
                    file_path=file_path,
                    replacements_made=replacements,
                    message=f"Successfully replaced {replacements} occurrence(s).",
                ),
            )

        except UnicodeDecodeError:
            return ToolResult(
                success=False,
                output=FileEditError(
                    file_path=file_path,
                    error="File appears to be binary or has encoding issues.",
                ),
            )
        except PermissionError:
            return ToolResult(
                success=False,
                output=FileEditError(
                    file_path=file_path,
                    error="Permission denied.",
                ),
            )
        except Exception as e:
            return ToolResult(
                success=False,
                output=FileEditError(
                    file_path=file_path,
                    error=str(e),
                ),
            )

    def get_path(self, input_data: FileEditInput) -> str:
        """Get the file path from input."""
        return input_data.path

    def user_facing_name(self, input_data: FileEditInput | None = None) -> str:
        """Get the user-facing name for this tool."""
        return "Edit"

    def get_tool_use_summary(self, input_data: FileEditInput | None) -> str | None:
        """Get a short summary of this tool use."""
        if input_data and input_data.path:
            return os.path.basename(input_data.path)
        return None

    def get_activity_description(self, input_data: FileEditInput | None) -> str | None:
        """Get a human-readable activity description."""
        if input_data and input_data.path:
            return f"Editing {os.path.basename(input_data.path)}"
        return "Editing file"
