"""Config tool implementation."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from ...core.tool import Tool, ToolCallProgress, ToolResult, ToolUseContext, ValidationResult
from .constants import CONFIG_TOOL_NAME, DESCRIPTION
from .prompt import generate_prompt
from .supported_settings import get_config, get_options_for_setting, is_supported


@dataclass
class ConfigToolInput:
    setting: str
    value: str | bool | int | float | None = None


@dataclass
class ConfigToolOutput:
    success: bool
    operation: str | None = None
    setting: str | None = None
    value: Any = None
    previous_value: Any = None
    new_value: Any = None
    error: str | None = None


INPUT_SCHEMA: dict[str, Any] = {
    "type": "object",
    "additionalProperties": False,
    "properties": {
        "setting": {
            "type": "string",
            "description": 'The setting key (e.g., "theme", "model", "permissions.defaultMode")',
        },
        "value": {
            "oneOf": [
                {"type": "string"},
                {"type": "boolean"},
                {"type": "number"},
            ],
            "description": "The new value. Omit to get current value.",
        },
    },
    "required": ["setting"],
}


class ConfigTool(Tool):
    """Tool for getting and setting configuration."""

    name = CONFIG_TOOL_NAME
    description = DESCRIPTION
    input_schema = INPUT_SCHEMA
    is_read_only = False
    is_concurrency_safe = True
    user_facing_name = "Config"

    def validate_input(self, input_data: dict[str, Any]) -> ValidationResult:
        setting = str(input_data.get("setting", "")).strip()
        if not setting:
            return ValidationResult(result=False, message="Setting key is required", error_code=1)
        if not is_supported(setting):
            return ValidationResult(
                result=False,
                message=f'Unknown setting: "{setting}"',
                error_code=2,
            )
        return ValidationResult(result=True)

    async def call(
        self,
        input_data: dict[str, Any],
        context: ToolUseContext,
        progress_callback: ToolCallProgress | None = None,
    ) -> ToolResult[ConfigToolOutput]:
        setting = str(input_data.get("setting", ""))
        value = input_data.get("value")
        cfg = get_config(setting)
        if not cfg:
            return ToolResult(
                data=ConfigToolOutput(success=False, error=f'Unknown setting: "{setting}"'),
            )

        if value is None:
            current = _get_in_memory_default(setting, cfg)
            display = cfg.format_on_read(current) if cfg.format_on_read else current
            return ToolResult(
                data=ConfigToolOutput(
                    success=True,
                    operation="get",
                    setting=setting,
                    value=display,
                ),
            )

        final_value: Any = value
        if cfg.type == "boolean" and isinstance(value, str):
            low = value.lower().strip()
            if low == "true":
                final_value = True
            elif low == "false":
                final_value = False

        if cfg.type == "boolean" and not isinstance(final_value, bool):
            return ToolResult(
                data=ConfigToolOutput(
                    success=False,
                    operation="set",
                    setting=setting,
                    error=f"{setting} requires true or false.",
                ),
            )

        options = get_options_for_setting(setting)
        if options is not None and str(final_value) not in options:
            return ToolResult(
                data=ConfigToolOutput(
                    success=False,
                    operation="set",
                    setting=setting,
                    error=f'Invalid value "{value}". Options: {", ".join(options)}',
                ),
            )

        previous = _get_in_memory_default(setting, cfg)
        return ToolResult(
            data=ConfigToolOutput(
                success=True,
                operation="set",
                setting=setting,
                previous_value=previous,
                new_value=final_value,
            ),
        )

    def get_tool_use_summary(self, input_data: dict[str, Any]) -> str:
        setting = input_data.get("setting", "?")
        value = input_data.get("value")
        if value is not None:
            return f"Config(set {setting}={value})"
        return f"Config(get {setting})"


def _get_in_memory_default(setting: str, cfg: Any) -> Any:
    """Until global/settings stores are wired, return registry-aware defaults."""
    if cfg.options:
        return cfg.options[0]
    if cfg.type == "boolean":
        return False
    return None


def tool_documentation_prompt() -> str:
    """Full model-facing documentation (mirrors TS generatePrompt)."""
    return generate_prompt()
