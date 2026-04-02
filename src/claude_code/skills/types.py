"""
Skill system types.

Dataclasses and protocols for skills, prompts, and command registration.

Migrated from: skills/bundledSkills.ts, skills/loadSkillsDir.ts (types)
"""

from __future__ import annotations

from collections.abc import Awaitable, Callable
from dataclasses import dataclass, field
from typing import Any, Literal, Protocol, TypedDict

LoadedFrom = Literal[
    "commands_DEPRECATED",
    "skills",
    "plugin",
    "managed",
    "bundled",
    "mcp",
]

SettingSource = Literal[
    "userSettings",
    "projectSettings",
    "localSettings",
    "flagSettings",
    "policySettings",
]

PromptSource = Literal[
    "userSettings",
    "projectSettings",
    "localSettings",
    "flagSettings",
    "policySettings",
    "plugin",
    "builtin",
    "mcp",
    "bundled",
]


class TextPromptBlock(TypedDict):
    type: Literal["text"]
    text: str


PromptContentBlock = TextPromptBlock


class ToolUseContext(Protocol):
    """Minimal context passed when resolving a bundled skill prompt."""

    messages: list[Any]
    options: Any

    def get_app_state(self) -> Any: ...


GetPromptForCommand = Callable[
    [str, ToolUseContext],
    Awaitable[list[PromptContentBlock]],
]


@dataclass
class ParsedSkillFrontmatter:
    """
    Normalized frontmatter for a skill or legacy command (disk or MCP metadata).

    Mirrors the return shape of TS ``parseSkillFrontmatterFields``.
    """

    display_name: str | None
    description: str
    has_user_specified_description: bool
    allowed_tools: list[str]
    argument_hint: str | None
    argument_names: list[str]
    when_to_use: str | None
    version: str | None
    model: str | None
    disable_model_invocation: bool
    user_invocable: bool
    hooks: dict[str, Any] | None
    execution_context: Literal["fork"] | None
    agent: str | None
    effort: Any
    shell: Any


@dataclass
class SkillCommand:
    """
    A prompt-type slash skill/command (disk-based, bundled, or MCP).

    Mirrors the TS `Command` shape for `type: 'prompt'`.
    """

    type: Literal["prompt"] = "prompt"
    name: str = ""
    description: str = ""
    aliases: list[str] | None = None
    has_user_specified_description: bool = False
    allowed_tools: list[str] = field(default_factory=list)
    argument_hint: str | None = None
    arg_names: list[str] | None = None
    when_to_use: str | None = None
    version: str | None = None
    model: str | None = None
    disable_model_invocation: bool = False
    user_invocable: bool = True
    context: Literal["inline", "fork"] | None = None
    agent: str | None = None
    effort: str | None = None
    paths: list[str] | None = None
    content_length: int = 0
    is_hidden: bool = False
    progress_message: str = "running"
    source: PromptSource = "bundled"
    loaded_from: LoadedFrom = "bundled"
    hooks: dict[str, Any] | None = None
    skill_root: str | None = None
    is_enabled: Callable[[], bool] | None = None
    get_prompt_for_command: GetPromptForCommand | None = None
    display_name: str | None = None

    def user_facing_name(self) -> str:
        return self.display_name or self.name


@dataclass(kw_only=True)
class BundledSkillDefinition:
    """Definition passed to `register_bundled_skill` (mirrors TS BundledSkillDefinition)."""

    name: str
    description: str
    aliases: list[str] | None = None
    when_to_use: str | None = None
    argument_hint: str | None = None
    allowed_tools: list[str] | None = None
    model: str | None = None
    disable_model_invocation: bool = False
    user_invocable: bool = True
    hooks: dict[str, Any] | None = None
    context: Literal["inline", "fork"] | None = None
    agent: str | None = None
    files: dict[str, str] | None = None
    is_enabled: Callable[[], bool] | None = None
    get_prompt_for_command: GetPromptForCommand = field(repr=False)

    def __post_init__(self) -> None:
        if self.allowed_tools is None:
            self.allowed_tools = []


# Backwards-compatible alias used by older Python modules
Skill = SkillCommand
