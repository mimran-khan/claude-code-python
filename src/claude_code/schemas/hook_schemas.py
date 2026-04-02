"""
Pydantic models for persisted hook commands (mirrors Zod in schemas/hooks.ts).
"""

from __future__ import annotations

from typing import Annotated, Any, Literal

from pydantic import BaseModel, ConfigDict, Field, TypeAdapter, field_validator

from ..hooks.types import HOOK_EVENTS
from ..utils.shell_providers import SHELL_TYPES


class BashCommandHook(BaseModel):
    model_config = ConfigDict(populate_by_name=True, extra="forbid")

    type: Literal["command"] = "command"
    command: str
    if_: str | None = Field(default=None, alias="if")
    shell: Literal["bash", "powershell"] | None = None
    timeout: float | None = Field(default=None, gt=0)
    status_message: str | None = None
    once: bool | None = None
    async_: bool | None = Field(default=None, alias="async")
    async_rewake: bool | None = None

    @field_validator("shell")
    @classmethod
    def _shell_must_be_allowed(cls, value: str | None) -> str | None:
        if value is not None and value not in SHELL_TYPES:
            raise ValueError(f"shell must be one of {SHELL_TYPES}, got {value!r}")
        return value


class PromptHook(BaseModel):
    model_config = ConfigDict(populate_by_name=True, extra="forbid")

    type: Literal["prompt"] = "prompt"
    prompt: str
    if_: str | None = Field(default=None, alias="if")
    timeout: float | None = Field(default=None, gt=0)
    model: str | None = None
    status_message: str | None = None
    once: bool | None = None


class HttpHook(BaseModel):
    model_config = ConfigDict(populate_by_name=True, extra="forbid")

    type: Literal["http"] = "http"
    url: str
    if_: str | None = Field(default=None, alias="if")
    timeout: float | None = Field(default=None, gt=0)
    headers: dict[str, str] | None = None
    allowed_env_vars: list[str] | None = None
    status_message: str | None = None
    once: bool | None = None


class AgentHook(BaseModel):
    model_config = ConfigDict(populate_by_name=True, extra="forbid")

    type: Literal["agent"] = "agent"
    prompt: str
    if_: str | None = Field(default=None, alias="if")
    timeout: float | None = Field(default=None, gt=0)
    model: str | None = None
    status_message: str | None = None
    once: bool | None = None


HookCommand = Annotated[
    BashCommandHook | PromptHook | HttpHook | AgentHook,
    Field(discriminator="type"),
]

_hook_command_adapter: TypeAdapter[HookCommand] = TypeAdapter(HookCommand)


class HookMatcher(BaseModel):
    model_config = ConfigDict(extra="forbid")

    matcher: str | None = None
    hooks: list[
        Annotated[
            BashCommandHook | PromptHook | HttpHook | AgentHook,
            Field(discriminator="type"),
        ]
    ]


HooksSettings = dict[str, list[HookMatcher]]


def parse_hook_command(raw: dict[str, Any]) -> HookCommand:
    """Parse and validate a single hook command object."""
    return _hook_command_adapter.validate_python(raw)


def parse_hooks_settings(raw: dict[str, Any]) -> HooksSettings:
    """Parse full hooks map; keys must be HookEvent names."""
    result: HooksSettings = {}
    for key, value in raw.items():
        if key not in HOOK_EVENTS:
            continue
        if not isinstance(value, list):
            continue
        result[key] = TypeAdapter(list[HookMatcher]).validate_python(value)
    return result
