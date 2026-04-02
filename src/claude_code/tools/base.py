"""
Base tool types and definitions.

Provides the base classes and types for all tools.

Migrated from: Tool.ts (793 lines) - Core types
"""

from __future__ import annotations

from abc import ABC, abstractmethod
from collections.abc import Awaitable, Callable
from dataclasses import dataclass, field
from typing import Any, Generic, TypeVar

# Type variables for generic tool types
InputT = TypeVar("InputT", bound=dict[str, Any])
OutputT = TypeVar("OutputT")


# Alias types for clarity
ToolInput = dict[str, Any]
ToolOutput = Any


@dataclass
class ToolUseContext:
    """Context provided to tool execution."""

    tool_use_id: str
    read_file_state: dict[str, Any] = field(default_factory=dict)
    get_app_state: Callable[[], Any] | None = None
    abort_signal: Any | None = None

    def get_cwd(self) -> str:
        """Get the current working directory."""
        from ..utils.cwd import get_cwd

        return get_cwd()


@dataclass
class ToolPermissionContext:
    """Permission context for tool execution."""

    always_allow_rules: dict[str, list[str]] = field(default_factory=dict)
    always_deny_rules: dict[str, list[str]] = field(default_factory=dict)
    always_ask_rules: dict[str, list[str]] = field(default_factory=dict)
    permission_mode: str = "default"
    additional_working_paths: list[str] = field(default_factory=list)


@dataclass
class ToolResult:
    """Result of a tool execution."""

    success: bool
    output: Any = None
    error: str | None = None
    error_code: int | None = None


@dataclass
class ToolValidationResult:
    """Result of synchronous tool input validation (pre-execute)."""

    valid: bool = True
    error: str | None = None
    message: str | None = None
    error_code: int | None = None


class Tool(ABC, Generic[InputT, OutputT]):
    """Base class for all tools."""

    @property
    @abstractmethod
    def name(self) -> str:
        """The unique name of the tool."""
        pass

    @property
    def search_hint(self) -> str | None:
        """Optional hint for tool search."""
        return None

    @property
    def max_result_size_chars(self) -> int:
        """Maximum size of result in characters."""
        return 100_000

    @property
    def strict(self) -> bool:
        """Whether to use strict input validation."""
        return False

    @abstractmethod
    async def description(self) -> str:
        """Get the tool description."""
        pass

    @abstractmethod
    async def prompt(self) -> str:
        """Get the tool prompt."""
        pass

    @abstractmethod
    def get_input_schema(self) -> dict[str, Any]:
        """Get the input schema for the tool."""
        pass

    @abstractmethod
    def get_output_schema(self) -> dict[str, Any]:
        """Get the output schema for the tool."""
        pass

    @abstractmethod
    async def execute(
        self,
        input: InputT,
        context: ToolUseContext,
    ) -> ToolResult:
        """Execute the tool with the given input."""
        pass

    def user_facing_name(self, input: InputT | None = None) -> str:
        """Get the user-facing name of the tool."""
        return self.name

    def get_tool_use_summary(self, input: InputT | None = None) -> str | None:
        """Get a summary of the tool use."""
        return None

    def get_activity_description(self, input: InputT | None = None) -> str:
        """Get a description of the tool activity."""
        summary = self.get_tool_use_summary(input)
        return f"Running {self.name}" + (f": {summary}" if summary else "")

    def get_path(self, input: InputT) -> str | None:
        """Get a path from the input, if applicable."""
        return None

    async def validate_input(
        self,
        input: InputT,
        context: ToolUseContext,
    ) -> dict[str, Any]:
        """Validate the input before execution."""
        return {"result": True}

    async def check_permissions(
        self,
        input: InputT,
        context: ToolUseContext,
    ) -> dict[str, Any]:
        """Check permissions for the tool execution."""
        return {"behavior": "allow"}

    def backfill_observable_input(self, input: InputT) -> None:
        """Backfill any observable input fields."""
        pass


@dataclass
class ToolDef:
    """Definition of a tool for registration."""

    name: str
    description: str | Callable[[], Awaitable[str]]
    prompt: str | Callable[[], Awaitable[str]]
    input_schema: dict[str, Any]
    output_schema: dict[str, Any] | None = None
    execute: Callable[[ToolInput, ToolUseContext], Awaitable[ToolResult]] | None = None
    user_facing_name: Callable[[ToolInput | None], str] | None = None
    get_tool_use_summary: Callable[[ToolInput | None], str | None] | None = None
    get_activity_description: Callable[[ToolInput | None], str] | None = None
    validate_input: Callable[[ToolInput, ToolUseContext], Awaitable[dict[str, Any]]] | None = None
    check_permissions: Callable[[ToolInput, ToolUseContext], Awaitable[dict[str, Any]]] | None = None
    search_hint: str | None = None
    max_result_size_chars: int = 100_000
    strict: bool = False


def build_tool(tool_def: ToolDef) -> Tool:
    """Build a Tool instance from a ToolDef."""

    class BuiltTool(Tool[ToolInput, Any]):
        @property
        def name(self) -> str:
            return tool_def.name

        @property
        def search_hint(self) -> str | None:
            return tool_def.search_hint

        @property
        def max_result_size_chars(self) -> int:
            return tool_def.max_result_size_chars

        @property
        def strict(self) -> bool:
            return tool_def.strict

        async def description(self) -> str:
            if callable(tool_def.description):
                return await tool_def.description()
            return tool_def.description

        async def prompt(self) -> str:
            if callable(tool_def.prompt):
                return await tool_def.prompt()
            return tool_def.prompt

        def get_input_schema(self) -> dict[str, Any]:
            return tool_def.input_schema

        def get_output_schema(self) -> dict[str, Any]:
            return tool_def.output_schema or {}

        async def execute(
            self,
            input: ToolInput,
            context: ToolUseContext,
        ) -> ToolResult:
            if tool_def.execute:
                return await tool_def.execute(input, context)
            return ToolResult(success=False, error="Not implemented")

        def user_facing_name(self, input: ToolInput | None = None) -> str:
            if tool_def.user_facing_name:
                return tool_def.user_facing_name(input)
            return tool_def.name

        def get_tool_use_summary(self, input: ToolInput | None = None) -> str | None:
            if tool_def.get_tool_use_summary:
                return tool_def.get_tool_use_summary(input)
            return None

        async def validate_input(
            self,
            input: ToolInput,
            context: ToolUseContext,
        ) -> dict[str, Any]:
            if tool_def.validate_input:
                return await tool_def.validate_input(input, context)
            return {"result": True}

        async def check_permissions(
            self,
            input: ToolInput,
            context: ToolUseContext,
        ) -> dict[str, Any]:
            if tool_def.check_permissions:
                return await tool_def.check_permissions(input, context)
            return {"behavior": "allow"}

    return BuiltTool()
