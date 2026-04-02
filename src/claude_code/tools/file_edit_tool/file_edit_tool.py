"""
File Edit Tool — migrated from tools/FileEditTool/FileEditTool.ts.

External integrations (LSP, analytics, team memory, permissions) are stubbed with TODOs.
"""

from __future__ import annotations

import asyncio
import os
from typing import Any

from ...utils.file import get_file_modification_time, write_text_content
from ...utils.path_utils import expand_path
from ..base import Tool, ToolResult, ToolUseContext
from .constants import FILE_EDIT_TOOL_NAME, FILE_UNEXPECTEDLY_MODIFIED_ERROR, MAX_EDIT_FILE_SIZE
from .edit_utils import find_actual_string, get_patch_for_edit, preserve_quote_style
from .prompt_text import get_edit_tool_description
from .types import FileEditOutputModel


class FileEditTool(Tool[dict[str, Any], FileEditOutputModel]):
    @property
    def name(self) -> str:
        return FILE_EDIT_TOOL_NAME

    @property
    def search_hint(self) -> str:
        return "modify file contents in place"

    @property
    def strict(self) -> bool:
        return True

    async def description(self) -> str:
        return "A tool for editing files"

    async def prompt(self) -> str:
        return get_edit_tool_description()

    def get_input_schema(self) -> dict[str, Any]:
        return {
            "type": "object",
            "additionalProperties": False,
            "properties": {
                "file_path": {
                    "type": "string",
                    "description": "The absolute path to the file to modify",
                },
                "old_string": {"type": "string", "description": "The text to replace"},
                "new_string": {
                    "type": "string",
                    "description": "The text to replace it with (must be different from old_string)",
                },
                "replace_all": {
                    "type": "boolean",
                    "description": "Replace all occurrences of old_string (default false)",
                    "default": False,
                },
            },
            "required": ["file_path", "old_string", "new_string"],
        }

    def get_output_schema(self) -> dict[str, Any]:
        return {
            "type": "object",
            "properties": {
                "filePath": {"type": "string"},
                "oldString": {"type": "string"},
                "newString": {"type": "string"},
                "originalFile": {"type": "string"},
                "structuredPatch": {"type": "array"},
                "userModified": {"type": "boolean"},
                "replaceAll": {"type": "boolean"},
                "gitDiff": {"type": "object"},
            },
        }

    def user_facing_name(self, input: dict[str, Any] | None = None) -> str:
        return FILE_EDIT_TOOL_NAME

    def get_tool_use_summary(self, input: dict[str, Any] | None = None) -> str | None:
        if input:
            return str(input.get("file_path", "")) or None
        return None

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
        old_string = str(input.get("old_string", ""))
        new_string = str(input.get("new_string", ""))
        replace_all = bool(input.get("replace_all", False))

        # TODO: checkTeamMemSecrets(full_path, new_string) — team memory guard (TS)

        if old_string == new_string:
            return {
                "result": False,
                "behavior": "ask",
                "message": "No changes to make: old_string and new_string are exactly the same.",
                "errorCode": 1,
            }

        full_path = expand_path(file_path)

        # TODO: matchingRuleForInput deny check via app permission context (TS)

        if full_path.startswith("\\\\") or full_path.startswith("//"):
            return {"result": True}

        try:
            st = await asyncio.to_thread(os.stat, full_path)
            if st.st_size > MAX_EDIT_FILE_SIZE:
                return {
                    "result": False,
                    "behavior": "ask",
                    "message": "File is too large to edit.",
                    "errorCode": 10,
                }
        except FileNotFoundError:
            pass

        try:

            def _read() -> str:
                with open(full_path, "rb") as f:
                    raw = f.read()
                enc = "utf-16-le" if len(raw) >= 2 and raw[0:2] == b"\xff\xfe" else "utf-8"
                return raw.decode(enc, errors="replace").replace("\r\n", "\n")

            file_content = await asyncio.to_thread(_read)
        except FileNotFoundError:
            if old_string == "":
                return {"result": True}
            return {
                "result": False,
                "behavior": "ask",
                "message": f"File does not exist: {file_path}",
                "errorCode": 4,
            }

        if old_string == "":
            if file_content.strip() != "":
                return {
                    "result": False,
                    "behavior": "ask",
                    "message": "Cannot create new file - file already exists.",
                    "errorCode": 3,
                }
            return {"result": True}

        if full_path.endswith(".ipynb"):
            return {
                "result": False,
                "behavior": "ask",
                "message": "File is a Jupyter Notebook. Use the NotebookEdit tool to edit this file.",
                "errorCode": 5,
            }

        rs = context.read_file_state.get(full_path)
        if not rs or rs.get("is_partial_view"):
            return {
                "result": False,
                "behavior": "ask",
                "message": "File has not been read yet. Read it first before writing to it.",
                "errorCode": 6,
            }

        last_write = get_file_modification_time(full_path)
        if rs:
            prev_ts = float(rs.get("timestamp", rs.get("mtime_ms", 0)))
            if last_write > prev_ts:
                is_full = rs.get("offset") is None and rs.get("limit") is None
                if not (is_full and file_content == rs.get("content")):
                    return {
                        "result": False,
                        "behavior": "ask",
                        "message": (
                            "File has been modified since read, either by the user or by a linter. "
                            "Read it again before attempting to write it."
                        ),
                        "errorCode": 7,
                    }

        actual_old = find_actual_string(file_content, old_string)
        if not actual_old:
            return {
                "result": False,
                "behavior": "ask",
                "message": f"String to replace not found in file.\nString: {old_string}",
                "errorCode": 8,
            }

        matches = file_content.count(actual_old)
        if matches > 1 and not replace_all:
            return {
                "result": False,
                "behavior": "ask",
                "message": (f"Found {matches} matches of the string to replace, but replace_all is false."),
                "errorCode": 9,
            }

        # TODO: validateInputForSettingsFileEdit (TS)

        return {"result": True, "meta": {"actualOldString": actual_old}}

    async def check_permissions(
        self,
        input: dict[str, Any],
        context: ToolUseContext,
    ) -> dict[str, Any]:
        # TODO: checkWritePermissionForTool(FileEditTool, ...) (TS)
        return {"behavior": "ask"}

    async def execute(
        self,
        input: dict[str, Any],
        context: ToolUseContext,
    ) -> ToolResult:
        file_path = str(input.get("file_path", ""))
        old_string = str(input.get("old_string", ""))
        new_string = str(input.get("new_string", ""))
        replace_all = bool(input.get("replace_all", False))
        absolute = expand_path(file_path)

        # TODO: discoverSkillDirsForPaths, addSkillDirectories, activateConditionalSkills (TS)
        # TODO: diagnosticTracker.beforeFileEdited (TS)

        parent = os.path.dirname(absolute)
        if parent:
            await asyncio.to_thread(os.makedirs, parent, exist_ok=True)

        # TODO: fileHistoryTrackEdit (TS)

        def _read_meta() -> tuple[str, bool]:
            try:
                with open(absolute, encoding="utf-8", errors="replace") as f:
                    return f.read(), True
            except FileNotFoundError:
                return "", False
            except UnicodeDecodeError:
                with open(absolute, "rb") as f:
                    raw = f.read()
                enc = "utf-16-le" if len(raw) >= 2 and raw[0:2] == b"\xff\xfe" else "utf-8"
                return raw.decode(enc, errors="replace").replace("\r\n", "\n"), True

        original, file_exists = await asyncio.to_thread(_read_meta)

        if file_exists:
            last_write = get_file_modification_time(absolute)
            last_read = context.read_file_state.get(absolute)
            lr_ts = float(last_read.get("timestamp", last_read.get("mtime_ms", 0))) if last_read else 0
            if not last_read or last_write > lr_ts:
                is_full = last_read and last_read.get("offset") is None and last_read.get("limit") is None
                unchanged = is_full and original == last_read.get("content")
                if not unchanged:
                    return ToolResult(
                        success=False,
                        error=FILE_UNEXPECTEDLY_MODIFIED_ERROR,
                        error_code=7,
                    )

        actual_old = find_actual_string(original, old_string) or old_string
        actual_new = preserve_quote_style(old_string, actual_old, new_string)

        try:
            patch, updated = get_patch_for_edit(
                absolute,
                original,
                actual_old,
                actual_new,
                replace_all,
            )
        except ValueError as e:
            return ToolResult(success=False, error=str(e), error_code=8)

        # TODO: writeTextContent with detected encoding/line endings from readFileSyncWithMetadata
        await asyncio.to_thread(write_text_content, absolute, updated, "utf-8", "LF")

        # TODO: LSP didChange/didSave, notifyVscodeFileUpdated (TS)
        # TODO: logEvent, countLinesChanged, logFileOperation (TS)
        # TODO: fetchSingleFileGitDiff when remote + feature flag (TS)

        context.read_file_state[absolute] = {
            "content": updated,
            "timestamp": get_file_modification_time(absolute),
            "offset": None,
            "limit": None,
        }

        out = FileEditOutputModel(
            file_path=file_path,
            old_string=actual_old,
            new_string=new_string,
            original_file=original,
            structured_patch=patch,
            user_modified=False,
            replace_all=replace_all,
            git_diff=None,
        )
        return ToolResult(success=True, output=out)


async def edit_file(input: dict[str, Any], context: ToolUseContext) -> ToolResult:
    """Execute FileEditTool without instantiating at call site."""
    return await FileEditTool().execute(input, context)
