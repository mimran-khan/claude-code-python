"""
Glob tool implementation.

Searches for files matching a glob pattern.

Migrated from: tools/GlobTool/GlobTool.ts
"""

from __future__ import annotations

import os
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from pydantic import BaseModel, Field

from ..base import Tool, ToolResult, ToolValidationResult
from .prompt import GLOB_TOOL_NAME


class GlobInput(BaseModel):
    """Input schema for the Glob tool."""

    glob_pattern: str = Field(
        ...,
        description="The glob pattern to match files against.",
    )
    target_directory: str | None = Field(
        None,
        description="Directory to search in (defaults to workspace root).",
    )


@dataclass
class GlobOutput:
    """Output from the Glob tool."""

    files: list[str]
    truncated: bool = False
    total_count: int = 0


class GlobTool(Tool[GlobInput, GlobOutput]):
    """
    Tool for searching files by glob pattern.

    Uses glob patterns to find files matching a pattern.
    """

    # Default limits
    DEFAULT_LIMIT = 100

    @property
    def name(self) -> str:
        return GLOB_TOOL_NAME

    @property
    def description(self) -> str:
        from .prompt import DESCRIPTION

        return DESCRIPTION

    def get_input_schema(self) -> dict[str, Any]:
        return GlobInput.model_json_schema()

    async def validate_input(
        self,
        input_data: GlobInput,
        context: Any,
    ) -> ToolValidationResult:
        """Validate the glob input."""
        if not input_data.glob_pattern:
            return ToolValidationResult(
                valid=False,
                error="glob_pattern is required",
            )

        return ToolValidationResult(valid=True)

    async def call(
        self,
        input_data: GlobInput,
        context: Any,
    ) -> ToolResult[GlobOutput]:
        """Execute the glob search."""
        pattern = input_data.glob_pattern
        target_dir = input_data.target_directory or os.getcwd()

        # Ensure target directory exists
        if not os.path.isdir(target_dir):
            return ToolResult(
                data=GlobOutput(files=[], truncated=False, total_count=0),
                error=f"Directory not found: {target_dir}",
            )

        # Prepend ** if pattern doesn't start with it
        if not pattern.startswith("**/"):
            pattern = f"**/{pattern}"

        try:
            path = Path(target_dir)
            all_files: list[str] = []

            for match in path.glob(pattern):
                if match.is_file():
                    # Get relative path if possible
                    try:
                        rel_path = match.relative_to(target_dir)
                        all_files.append(str(rel_path))
                    except ValueError:
                        all_files.append(str(match))

            # Sort by modification time (newest first)
            def get_mtime(f: str) -> float:
                try:
                    full_path = os.path.join(target_dir, f)
                    return os.path.getmtime(full_path)
                except Exception:
                    return 0

            all_files.sort(key=get_mtime, reverse=True)

            # Apply limit
            truncated = len(all_files) > self.DEFAULT_LIMIT
            files = all_files[: self.DEFAULT_LIMIT]

            return ToolResult(
                data=GlobOutput(
                    files=files,
                    truncated=truncated,
                    total_count=len(all_files),
                )
            )

        except Exception as e:
            return ToolResult(
                data=GlobOutput(files=[], truncated=False, total_count=0),
                error=str(e),
            )
