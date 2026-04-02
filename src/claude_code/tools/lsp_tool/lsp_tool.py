"""LSP Tool implementation for Language Server Protocol operations."""

from dataclasses import dataclass
from typing import Any

from ...core.tool import Tool, ToolCallProgress, ToolResult, ToolUseContext, ValidationResult

LSP_TOOL_NAME = "LSP"

DESCRIPTION = "Perform Language Server Protocol operations"

LSP_OPERATIONS = (
    "goToDefinition",
    "findReferences",
    "hover",
    "documentSymbol",
    "workspaceSymbol",
    "goToImplementation",
    "prepareCallHierarchy",
    "incomingCalls",
    "outgoingCalls",
)


@dataclass
class LSPLocation:
    """LSP location result."""

    file: str
    line: int
    character: int


@dataclass
class LSPSymbol:
    """LSP symbol result."""

    name: str
    kind: str
    location: LSPLocation


@dataclass
class LSPHover:
    """LSP hover result."""

    contents: str
    range_start: LSPLocation | None = None
    range_end: LSPLocation | None = None


@dataclass
class LSPOutput:
    """Output from LSP tool."""

    operation: str
    success: bool
    results: list[Any] | None = None
    hover: LSPHover | None = None
    error: str | None = None


INPUT_SCHEMA = {
    "type": "object",
    "properties": {
        "operation": {
            "type": "string",
            "enum": list(LSP_OPERATIONS),
            "description": "The LSP operation to perform",
        },
        "filePath": {
            "type": "string",
            "description": "The absolute or relative path to the file",
        },
        "line": {
            "type": "integer",
            "minimum": 1,
            "description": "The line number (1-based, as shown in editors)",
        },
        "character": {
            "type": "integer",
            "minimum": 1,
            "description": "The character offset (1-based, as shown in editors)",
        },
    },
    "required": ["operation", "filePath", "line", "character"],
}


class LSPTool(Tool):
    """Tool for LSP operations."""

    name = LSP_TOOL_NAME
    description = DESCRIPTION
    input_schema = INPUT_SCHEMA
    is_read_only = True
    is_concurrency_safe = True
    user_facing_name = "LSP"

    def validate_input(self, input_data: dict[str, Any]) -> ValidationResult:
        """Validate the input."""
        operation = input_data.get("operation", "")
        if operation not in LSP_OPERATIONS:
            return ValidationResult(
                result=False,
                message=f"Invalid operation: {operation}. Valid: {', '.join(LSP_OPERATIONS)}",
                error_code=1,
            )

        file_path = input_data.get("filePath", "")
        if not file_path:
            return ValidationResult(
                result=False,
                message="filePath is required",
                error_code=2,
            )

        line = input_data.get("line", 0)
        if line < 1:
            return ValidationResult(
                result=False,
                message="line must be >= 1",
                error_code=3,
            )

        character = input_data.get("character", 0)
        if character < 1:
            return ValidationResult(
                result=False,
                message="character must be >= 1",
                error_code=4,
            )

        return ValidationResult(result=True)

    async def call(
        self,
        input_data: dict[str, Any],
        context: ToolUseContext,
        progress_callback: ToolCallProgress | None = None,
    ) -> ToolResult[LSPOutput]:
        """Execute the LSP operation."""
        operation = input_data.get("operation", "")
        input_data.get("filePath", "")
        input_data.get("line", 1)
        input_data.get("character", 1)

        # In full implementation, this would:
        # 1. Check if LSP server is connected
        # 2. Wait for initialization
        # 3. Send the appropriate LSP request
        # 4. Format and return the response

        # Stub implementation
        return ToolResult(
            data=LSPOutput(
                operation=operation,
                success=False,
                error="LSP server not connected (stub implementation)",
            )
        )

    def get_tool_use_summary(self, input_data: dict[str, Any]) -> str:
        """Get a summary of the tool use."""
        operation = input_data.get("operation", "?")
        file_path = input_data.get("filePath", "?")
        line = input_data.get("line", "?")

        # Shorten file path
        if len(file_path) > 30:
            file_path = "..." + file_path[-27:]

        return f"LSP({operation} {file_path}:{line})"
