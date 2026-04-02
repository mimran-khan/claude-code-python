"""
List code definitions — conceptual port of an LSP documentSymbol-style tool.

TODO: Wire getLspServerManager().documentSymbols (tools/LSPTool/*) or tree-sitter fallback.
"""

from __future__ import annotations

from typing import Any

from ...utils.path_utils import expand_path
from ..base import Tool, ToolResult, ToolUseContext
from .constants import DESCRIPTION, LIST_CODE_DEFINITION_TOOL_NAME
from .types import ListCodeDefinitionOutput


class ListCodeDefinitionTool(Tool[dict[str, Any], ListCodeDefinitionOutput]):
    @property
    def name(self) -> str:
        return LIST_CODE_DEFINITION_TOOL_NAME

    @property
    def search_hint(self) -> str:
        return "list symbols definitions outline in file"

    async def description(self) -> str:
        return DESCRIPTION

    async def prompt(self) -> str:
        return DESCRIPTION

    def get_input_schema(self) -> dict[str, Any]:
        return {
            "type": "object",
            "properties": {
                "file_path": {"type": "string", "description": "Absolute path to source file"},
                "depth": {"type": "integer", "description": "Max nesting depth for symbol tree"},
            },
            "required": ["file_path"],
        }

    def get_output_schema(self) -> dict[str, Any]:
        return {
            "type": "object",
            "properties": {
                "file_path": {"type": "string"},
                "symbols": {"type": "array"},
            },
        }

    def get_path(self, input: dict[str, Any]) -> str | None:
        return input.get("file_path")

    async def check_permissions(
        self,
        input: dict[str, Any],
        context: ToolUseContext,
    ) -> dict[str, Any]:
        # TODO: checkReadPermissionForTool (TS)
        return {"behavior": "allow"}

    async def execute(
        self,
        input: dict[str, Any],
        context: ToolUseContext,
    ) -> ToolResult:
        fp = expand_path(str(input.get("file_path", "")))
        # TODO: LSP documentSymbol request
        out = ListCodeDefinitionOutput(file_path=fp, symbols=[], raw=None)
        return ToolResult(success=True, output=out)
