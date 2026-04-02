"""
Structured (synthetic) output tool for non-interactive SDK sessions.

Migrated from: tools/SyntheticOutputTool/SyntheticOutputTool.ts
"""

from __future__ import annotations

import json
from dataclasses import dataclass
from typing import Any

from jsonschema import Draft202012Validator
from jsonschema.exceptions import SchemaError

from ...core.tool import Tool, ToolCallProgress, ToolResult, ToolUseContext, ValidationResult

SYNTHETIC_OUTPUT_TOOL_NAME = "StructuredOutput"

_validator_cache: dict[str, Draft202012Validator] = {}


def _cache_key(schema: dict[str, Any]) -> str:
    return json.dumps(schema, sort_keys=True, default=str)


@dataclass
class SyntheticStructuredResult:
    message: str
    structured_output: dict[str, Any]


def is_synthetic_output_tool_enabled(*, is_non_interactive_session: bool) -> bool:
    return is_non_interactive_session


class SyntheticOutputTool(Tool):
    name = SYNTHETIC_OUTPUT_TOOL_NAME
    description = "Return structured output in the requested format"
    input_schema: dict[str, Any] = {"type": "object", "additionalProperties": True}
    is_read_only = True
    is_concurrency_safe = True

    async def call(
        self,
        input_data: dict[str, Any],
        context: ToolUseContext,
        progress_callback: ToolCallProgress | None = None,
    ) -> ToolResult[SyntheticStructuredResult]:
        return ToolResult(
            data=SyntheticStructuredResult(
                message="Structured output provided successfully",
                structured_output=dict(input_data),
            ),
        )

    def validate_input(self, input_data: dict[str, Any]) -> ValidationResult:
        return ValidationResult(result=True)


@dataclass
class CreateSyntheticOutputToolResult:
    tool: Tool | None = None
    error: str | None = None


def _make_validating_tool(validator: Draft202012Validator, schema: dict[str, Any]) -> type[Tool]:
    class SchemaSyntheticTool(Tool):
        name = SYNTHETIC_OUTPUT_TOOL_NAME
        description = SyntheticOutputTool.description
        input_schema = schema
        is_read_only = True
        is_concurrency_safe = True

        async def call(
            self,
            input_data: dict[str, Any],
            context: ToolUseContext,
            progress_callback: ToolCallProgress | None = None,
        ) -> ToolResult[SyntheticStructuredResult]:
            errors = sorted(validator.iter_errors(input_data), key=lambda e: list(e.path))
            if errors:
                msg = ", ".join(f"{list(e.path)}: {e.message}" for e in errors)
                raise ValueError(f"Output does not match required schema: {msg}")
            return ToolResult(
                data=SyntheticStructuredResult(
                    message="Structured output provided successfully",
                    structured_output=dict(input_data),
                ),
            )

    return SchemaSyntheticTool


def create_synthetic_output_tool(
    json_schema: dict[str, Any],
) -> CreateSyntheticOutputToolResult:
    key = _cache_key(json_schema)
    try:
        Draft202012Validator.check_schema(json_schema)
    except SchemaError as e:
        return CreateSyntheticOutputToolResult(error=str(e))

    validator = _validator_cache.get(key)
    if validator is None:
        validator = Draft202012Validator(json_schema)
        _validator_cache[key] = validator

    cls = _make_validating_tool(validator, json_schema)
    return CreateSyntheticOutputToolResult(tool=cls())
