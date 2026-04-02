"""
Grep tool implementation.

Searches for content matching a regex pattern.

Migrated from: tools/GrepTool/GrepTool.ts
"""

from __future__ import annotations

import contextlib
import os
import re
from dataclasses import dataclass
from typing import Any, Literal

from pydantic import BaseModel, Field

from ...utils.ripgrep import ripgrep
from ..base import Tool, ToolResult, ToolValidationResult
from .prompt import GREP_TOOL_NAME


class GrepInput(BaseModel):
    """Input schema for the Grep tool."""

    pattern: str = Field(
        ...,
        description="The regex pattern to search for.",
    )
    path: str | None = Field(
        None,
        description="File or directory to search in.",
    )
    glob: str | None = Field(
        None,
        description="Glob pattern to filter files.",
    )
    type: str | None = Field(
        None,
        description="File type to search (e.g., 'js', 'py').",
    )
    output_mode: Literal["content", "files_with_matches", "count"] = Field(
        "content",
        description="Output mode.",
    )
    case_insensitive: bool = Field(
        False,
        alias="-i",
        description="Case insensitive search.",
    )
    context_before: int | None = Field(
        None,
        alias="-B",
        description="Lines of context before matches.",
    )
    context_after: int | None = Field(
        None,
        alias="-A",
        description="Lines of context after matches.",
    )
    context: int | None = Field(
        None,
        alias="-C",
        description="Lines of context before and after.",
    )
    head_limit: int | None = Field(
        None,
        description="Limit number of results.",
    )
    multiline: bool = Field(
        False,
        description="Enable multiline matching.",
    )


@dataclass
class GrepMatch:
    """A grep match result."""

    file: str
    line_number: int
    content: str


@dataclass
class GrepOutput:
    """Output from the Grep tool."""

    matches: list[GrepMatch]
    file_counts: dict[str, int] | None = None
    files_with_matches: list[str] | None = None
    truncated: bool = False


class GrepTool(Tool[GrepInput, GrepOutput]):
    """
    Tool for searching file content using regex.

    Uses ripgrep for fast searching with full regex support.
    """

    DEFAULT_LIMIT = 1000

    @property
    def name(self) -> str:
        return GREP_TOOL_NAME

    @property
    def description(self) -> str:
        from .prompt import get_description

        return get_description()

    def get_input_schema(self) -> dict[str, Any]:
        return GrepInput.model_json_schema()

    async def validate_input(
        self,
        input_data: GrepInput,
        context: Any,
    ) -> ToolValidationResult:
        """Validate the grep input."""
        if not input_data.pattern:
            return ToolValidationResult(
                valid=False,
                error="pattern is required",
            )

        # Validate regex
        try:
            re.compile(input_data.pattern)
        except re.error as e:
            return ToolValidationResult(
                valid=False,
                error=f"Invalid regex pattern: {e}",
            )

        return ToolValidationResult(valid=True)

    async def call(
        self,
        input_data: GrepInput,
        context: Any,
    ) -> ToolResult[GrepOutput]:
        """Execute the grep search."""
        pattern = input_data.pattern
        path = input_data.path or os.getcwd()

        # Build ripgrep arguments
        args: list[str] = []

        # Output mode
        if input_data.output_mode == "files_with_matches":
            args.append("--files-with-matches")
        elif input_data.output_mode == "count":
            args.append("--count")
        else:
            # Default content mode
            args.append("--line-number")

        # Case insensitive
        if input_data.case_insensitive:
            args.append("-i")

        # Context lines
        if input_data.context:
            args.extend(["-C", str(input_data.context)])
        elif input_data.context_before:
            args.extend(["-B", str(input_data.context_before)])
        elif input_data.context_after:
            args.extend(["-A", str(input_data.context_after)])

        # Glob filter
        if input_data.glob:
            args.extend(["--glob", input_data.glob])

        # File type
        if input_data.type:
            args.extend(["--type", input_data.type])

        # Multiline
        if input_data.multiline:
            args.append("-U")
            args.append("--multiline-dotall")

        # Add pattern
        args.append(pattern)

        try:
            lines = await ripgrep(args, path)

            # Parse results based on output mode
            if input_data.output_mode == "files_with_matches":
                files = lines[: input_data.head_limit or self.DEFAULT_LIMIT]
                return ToolResult(
                    data=GrepOutput(
                        matches=[],
                        files_with_matches=files,
                        truncated=len(lines) > len(files),
                    )
                )

            if input_data.output_mode == "count":
                file_counts: dict[str, int] = {}
                for line in lines:
                    if ":" in line:
                        file, count_str = line.rsplit(":", 1)
                        with contextlib.suppress(ValueError):
                            file_counts[file] = int(count_str)
                return ToolResult(
                    data=GrepOutput(
                        matches=[],
                        file_counts=file_counts,
                    )
                )

            # Parse content matches
            matches: list[GrepMatch] = []
            limit = input_data.head_limit or self.DEFAULT_LIMIT

            for line in lines:
                if len(matches) >= limit:
                    break

                # Parse line format: file:line_number:content
                parts = line.split(":", 2)
                if len(parts) >= 3:
                    with contextlib.suppress(ValueError):
                        matches.append(
                            GrepMatch(
                                file=parts[0],
                                line_number=int(parts[1]),
                                content=parts[2],
                            )
                        )

            return ToolResult(
                data=GrepOutput(
                    matches=matches,
                    truncated=len(lines) > len(matches),
                )
            )

        except Exception as e:
            return ToolResult(
                data=GrepOutput(matches=[]),
                error=str(e),
            )
