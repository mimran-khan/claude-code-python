"""
Config Tool Implementation.

Get or set Claude Code configuration settings.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Literal

from pydantic import BaseModel, Field

from ..base import Tool, ToolResult
from .prompt import CONFIG_TOOL_NAME, DESCRIPTION, SUPPORTED_SETTINGS


class ConfigInput(BaseModel):
    """Input parameters for config tool."""

    setting: str = Field(
        ...,
        description="The setting name to get or set.",
    )
    value: Any = Field(
        default=None,
        description="The value to set. Omit to get current value.",
    )


@dataclass
class ConfigGetResult:
    """Result of getting a config value."""

    type: Literal["get"] = "get"
    setting: str = ""
    value: Any = None
    source: str = ""


@dataclass
class ConfigSetResult:
    """Result of setting a config value."""

    type: Literal["set"] = "set"
    setting: str = ""
    old_value: Any = None
    new_value: Any = None


@dataclass
class ConfigError:
    """Config operation error."""

    type: Literal["error"] = "error"
    setting: str = ""
    error: str = ""


ConfigOutput = ConfigGetResult | ConfigSetResult | ConfigError


class ConfigTool(Tool[ConfigInput, ConfigOutput]):
    """
    Tool for getting and setting configuration.

    Supports both global settings (in ~/.claude.json) and
    project settings (in settings.json).
    """

    _config: dict[str, Any] = {}

    @property
    def name(self) -> str:
        return CONFIG_TOOL_NAME

    @property
    def description(self) -> str:
        return DESCRIPTION

    @property
    def input_schema(self) -> dict[str, Any]:
        return {
            "type": "object",
            "properties": {
                "setting": {
                    "type": "string",
                    "description": "The setting name to get or set.",
                },
                "value": {
                    "description": "The value to set. Omit to get current value.",
                },
            },
            "required": ["setting"],
        }

    def is_read_only(self, input_data: ConfigInput) -> bool:
        return input_data.value is None

    async def call(
        self,
        input_data: ConfigInput,
        context: Any,
    ) -> ToolResult[ConfigOutput]:
        """Execute the config operation."""
        setting = input_data.setting
        value = input_data.value

        # Check if setting is supported
        if setting not in SUPPORTED_SETTINGS:
            return ToolResult(
                success=False,
                output=ConfigError(
                    setting=setting,
                    error=f"Unknown setting: {setting}. Supported: {', '.join(SUPPORTED_SETTINGS.keys())}",
                ),
            )

        config_def = SUPPORTED_SETTINGS[setting]

        # Get operation
        if value is None:
            current_value = self._config.get(setting)
            return ToolResult(
                success=True,
                output=ConfigGetResult(
                    setting=setting,
                    value=current_value,
                    source=config_def["source"],
                ),
            )

        # Set operation - validate value
        if config_def["type"] == "boolean" and not isinstance(value, bool):
            return ToolResult(
                success=False,
                output=ConfigError(
                    setting=setting,
                    error=f"Setting {setting} requires a boolean value.",
                ),
            )

        if "options" in config_def and value not in config_def["options"]:
            return ToolResult(
                success=False,
                output=ConfigError(
                    setting=setting,
                    error=f"Invalid value for {setting}. Options: {config_def['options']}",
                ),
            )

        old_value = self._config.get(setting)
        self._config[setting] = value

        return ToolResult(
            success=True,
            output=ConfigSetResult(
                setting=setting,
                old_value=old_value,
                new_value=value,
            ),
        )

    def user_facing_name(self, input_data: ConfigInput | None = None) -> str:
        """Get the user-facing name for this tool."""
        return "Config"

    def get_tool_use_summary(self, input_data: ConfigInput | None) -> str | None:
        """Get a short summary of this tool use."""
        if input_data:
            if input_data.value is not None:
                return f"set {input_data.setting}"
            return f"get {input_data.setting}"
        return None
