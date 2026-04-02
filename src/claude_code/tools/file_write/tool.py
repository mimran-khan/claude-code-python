"""
FileWrite tool implementation.

Writes content to files.

Migrated from: tools/FileWriteTool/FileWriteTool.ts
"""

from __future__ import annotations

import os
from dataclasses import dataclass
from typing import Any

import aiofiles
from pydantic import BaseModel, Field

from ..base import Tool, ToolResult, ToolValidationResult
from .prompt import FILE_WRITE_TOOL_NAME


class FileWriteInput(BaseModel):
    """Input schema for the FileWrite tool."""

    path: str = Field(
        ...,
        description="The absolute path of the file to write.",
    )
    contents: str = Field(
        ...,
        description="The contents to write to the file.",
    )


@dataclass
class FileWriteOutput:
    """Output from the FileWrite tool."""

    success: bool
    path: str
    bytes_written: int = 0


class FileWriteTool(Tool[FileWriteInput, FileWriteOutput]):
    """
    Tool for writing files.

    Creates or overwrites files with the specified content.
    """

    @property
    def name(self) -> str:
        return FILE_WRITE_TOOL_NAME

    @property
    def description(self) -> str:
        from .prompt import get_write_tool_description

        return get_write_tool_description()

    def get_input_schema(self) -> dict[str, Any]:
        return FileWriteInput.model_json_schema()

    async def validate_input(
        self,
        input_data: FileWriteInput,
        context: Any,
    ) -> ToolValidationResult:
        """Validate the write input."""
        if not input_data.path:
            return ToolValidationResult(
                valid=False,
                error="path is required",
            )

        # Check if path is absolute
        if not os.path.isabs(input_data.path):
            return ToolValidationResult(
                valid=False,
                error="path must be absolute",
            )

        return ToolValidationResult(valid=True)

    async def call(
        self,
        input_data: FileWriteInput,
        context: Any,
    ) -> ToolResult[FileWriteOutput]:
        """Write content to the file."""
        path = input_data.path
        contents = input_data.contents

        try:
            # Ensure parent directory exists
            parent_dir = os.path.dirname(path)
            if parent_dir and not os.path.exists(parent_dir):
                os.makedirs(parent_dir, exist_ok=True)

            # Write the file
            async with aiofiles.open(path, "w", encoding="utf-8") as f:
                await f.write(contents)

            bytes_written = len(contents.encode("utf-8"))

            return ToolResult(
                data=FileWriteOutput(
                    success=True,
                    path=path,
                    bytes_written=bytes_written,
                )
            )

        except PermissionError:
            return ToolResult(
                data=FileWriteOutput(success=False, path=path),
                error=f"Permission denied: {path}",
            )
        except OSError as e:
            return ToolResult(
                data=FileWriteOutput(success=False, path=path),
                error=f"Failed to write file: {e}",
            )
        except Exception as e:
            return ToolResult(
                data=FileWriteOutput(success=False, path=path),
                error=str(e),
            )
