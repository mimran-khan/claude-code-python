"""
Edit files via exact string replacement.

Migrated from: tools/FileEditTool/FileEditTool.ts
"""

from __future__ import annotations

import os
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from ...core.tool import Tool, ToolCallProgress, ToolResult, ToolUseContext, ValidationResult
from .constants import EDIT_FILE_TOOL_NAME

# TODO: VSCode notify, file history / undo (TS fileHistoryTrackEdit, notifyVscodeFileUpdated).


@dataclass
class EditFileOutput:
    file_path: str
    replacements_made: int


INPUT_SCHEMA: dict[str, Any] = {
    "type": "object",
    "additionalProperties": False,
    "properties": {
        "path": {"type": "string", "description": "Absolute path to the file to modify"},
        "old_string": {
            "type": "string",
            "description": "Text to replace (must be unique unless replace_all)",
        },
        "new_string": {"type": "string", "description": "Replacement text"},
        "replace_all": {"type": "boolean", "default": False},
    },
    "required": ["path", "old_string", "new_string"],
}


class EditFileTool(Tool):
    name = EDIT_FILE_TOOL_NAME
    description = (
        "Performs exact string replacements in files. old_string must match exactly; "
        "use replace_all to change every occurrence."
    )
    input_schema = INPUT_SCHEMA
    is_read_only = False
    is_concurrency_safe = False
    user_facing_name = EDIT_FILE_TOOL_NAME

    def validate_input(self, input_data: dict[str, Any]) -> ValidationResult:
        path = input_data.get("path", "")
        old = input_data.get("old_string", "")
        new = input_data.get("new_string", "")
        if not isinstance(path, str) or not path.strip():
            return ValidationResult(result=False, message="path is required", error_code=1)
        if old == new:
            return ValidationResult(
                result=False,
                message="old_string and new_string cannot be identical",
                error_code=1,
            )
        p = Path(path).expanduser()
        if not p.is_file():
            return ValidationResult(result=False, message=f"File not found: {path}", error_code=1)
        return ValidationResult(result=True)

    async def call(
        self,
        input_data: dict[str, Any],
        context: ToolUseContext,
        progress_callback: ToolCallProgress | None = None,
    ) -> ToolResult[EditFileOutput]:
        _ = context, progress_callback
        path = str(input_data.get("path", ""))
        old_string = str(input_data.get("old_string", ""))
        new_string = str(input_data.get("new_string", ""))
        replace_all = bool(input_data.get("replace_all", False))

        full_path = Path(path).expanduser().resolve()

        try:
            content = full_path.read_text(encoding="utf-8")
        except UnicodeDecodeError:
            raise RuntimeError("File appears to be binary or has encoding issues.") from None

        if old_string not in content:
            raise RuntimeError(
                "old_string not found in file. Match whitespace and indentation exactly.",
            )

        count = content.count(old_string)
        if not replace_all and count > 1:
            raise RuntimeError(
                f"old_string appears {count} times; use replace_all or add context for uniqueness.",
            )

        if replace_all:
            new_content = content.replace(old_string, new_string)
            replacements = count
        else:
            new_content = content.replace(old_string, new_string, 1)
            replacements = 1

        full_path.write_text(new_content, encoding="utf-8")
        return ToolResult(
            data=EditFileOutput(file_path=str(full_path), replacements_made=replacements),
        )

    def get_tool_use_summary(self, input_data: dict[str, Any]) -> str:
        p = input_data.get("path")
        if isinstance(p, str) and p:
            return os.path.basename(p)
        return EDIT_FILE_TOOL_NAME
