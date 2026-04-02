"""
Local session-style memory files (user/project scoped).

There is no standalone MemoryTool in the leaked TS tree; this mirrors
FileReadTool session-memory paths and agent-memory style persistence in Python.
"""

from __future__ import annotations

import os
from dataclasses import asdict, dataclass
from typing import Any, Literal

from ..base import Tool, ToolResult, ToolUseContext

MEMORY_TOOL_NAME = "Memory"


@dataclass
class MemoryToolInput:
    """Structured input for memory operations."""

    action: Literal["read", "write", "list"]
    relative_path: str
    content: str | None = None


@dataclass
class MemoryToolOutput:
    action: str
    path: str
    content: str | None = None
    entries: list[str] | None = None


class MemoryTool(Tool[dict[str, Any], dict[str, Any]]):
    """Read/write markdown snippets under ~/.claude/session-memory (safe subpaths only)."""

    @property
    def name(self) -> str:
        return MEMORY_TOOL_NAME

    @property
    def search_hint(self) -> str | None:
        return "session memory files, persistent notes"

    async def description(self) -> str:
        return (
            "Read, write, or list markdown memory files under the Claude session-memory directory. "
            "Paths must be relative and must not escape the base directory."
        )

    async def prompt(self) -> str:
        return await self.description()

    def get_input_schema(self) -> dict[str, Any]:
        return {
            "type": "object",
            "additionalProperties": False,
            "properties": {
                "action": {"type": "string", "enum": ["read", "write", "list"]},
                "relative_path": {
                    "type": "string",
                    "description": "Path relative to session-memory, e.g. notes/feature-x.md",
                },
                "content": {"type": "string", "description": "Required for write"},
            },
            "required": ["action", "relative_path"],
        }

    def get_output_schema(self) -> dict[str, Any]:
        return {"type": "object", "additionalProperties": True}

    def _base_dir(self) -> str:
        try:
            from ...utils.config_utils import get_claude_config_dir
        except ImportError:
            return os.path.join(os.path.expanduser("~"), ".claude", "session-memory")
        return os.path.join(get_claude_config_dir(), "session-memory")

    def _safe_join(self, relative: str) -> str | None:
        rel = relative.strip().replace("\\", "/").lstrip("/")
        if not rel or ".." in rel.split("/"):
            return None
        base = os.path.abspath(self._base_dir())
        full = os.path.abspath(os.path.join(base, rel))
        if not full.startswith(base + os.sep) and full != base:
            return None
        return full

    async def execute(
        self,
        input: dict[str, Any],
        context: ToolUseContext,
    ) -> ToolResult:
        _ = context
        action = str(input.get("action", ""))
        rel = str(input.get("relative_path", ""))
        content = input.get("content")

        path = self._safe_join(rel)
        if path is None:
            return ToolResult(success=False, error="Invalid or unsafe relative_path")

        if action == "list":
            parent = path if os.path.isdir(path) else os.path.dirname(path)
            if not parent or not os.path.isdir(parent):
                try:
                    os.makedirs(parent or self._base_dir(), exist_ok=True)
                except OSError as e:
                    return ToolResult(success=False, error=str(e))
            try:
                entries = sorted(os.listdir(parent))
            except OSError as e:
                return ToolResult(success=False, error=str(e))
            out = MemoryToolOutput(action=action, path=parent, entries=entries)
            return ToolResult(success=True, output=asdict(out))

        if action == "read":
            if not os.path.isfile(path):
                return ToolResult(success=False, error=f"File not found: {rel}")
            try:
                with open(path, encoding="utf-8", errors="replace") as f:
                    text = f.read()
            except OSError as e:
                return ToolResult(success=False, error=str(e))
            out = MemoryToolOutput(action=action, path=path, content=text)
            return ToolResult(success=True, output=asdict(out))

        if action == "write":
            if content is None:
                return ToolResult(success=False, error="write requires content")
            text = str(content)
            try:
                os.makedirs(os.path.dirname(path), exist_ok=True)
                with open(path, "w", encoding="utf-8") as f:
                    f.write(text)
            except OSError as e:
                return ToolResult(success=False, error=str(e))
            out = MemoryToolOutput(action=action, path=path, content=text)
            return ToolResult(success=True, output=asdict(out))

        return ToolResult(success=False, error=f"Unknown action: {action}")
