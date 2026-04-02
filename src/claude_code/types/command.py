"""
Command type definitions.

This module defines types for slash commands, prompt commands, and
local commands that users can invoke in Claude Code.

Migrated from: types/command.ts (217 lines)
"""

from __future__ import annotations

from collections.abc import Awaitable, Callable
from dataclasses import dataclass
from typing import (
    TYPE_CHECKING,
    Any,
    Literal,
)

if TYPE_CHECKING:
    pass


# ============================================================================
# Command Result Types
# ============================================================================


@dataclass
class TextCommandResult:
    """Text result from a local command."""

    type: Literal["text"] = "text"
    value: str = ""


@dataclass
class CompactionResult:
    """Result of context compaction."""

    pass  # Will be defined in services/compact


@dataclass
class CompactCommandResult:
    """Compact result from a local command."""

    type: Literal["compact"] = "compact"
    compaction_result: CompactionResult | None = None
    display_text: str | None = None


@dataclass
class SkipCommandResult:
    """Skip result - command produces no output."""

    type: Literal["skip"] = "skip"


LocalCommandResult = TextCommandResult | CompactCommandResult | SkipCommandResult


# ============================================================================
# Setting Source
# ============================================================================

SettingSource = Literal[
    "userSettings",
    "projectSettings",
    "localSettings",
    "flagSettings",
    "policySettings",
    "cliArg",
]


# ============================================================================
# Resume Entrypoint
# ============================================================================

ResumeEntrypoint = Literal[
    "cli_flag",
    "slash_command_picker",
    "slash_command_session_id",
    "slash_command_title",
    "fork",
]


# ============================================================================
# Command Result Display
# ============================================================================

CommandResultDisplay = Literal["skip", "system", "user"]


# ============================================================================
# Effort Value
# ============================================================================

EffortValue = Literal["low", "medium", "high"]


# ============================================================================
# Plugin Info
# ============================================================================


@dataclass
class PluginInfo:
    """Information about the plugin a command comes from."""

    plugin_manifest: Any  # PluginManifest
    repository: str = ""


# ============================================================================
# Command Availability
# ============================================================================

CommandAvailability = Literal["claude-ai", "console"]


# ============================================================================
# Prompt Command
# ============================================================================


@dataclass
class PromptCommand:
    """
    A prompt command that sends content to the model.

    Prompt commands generate prompts that are sent to Claude for processing.
    """

    type: Literal["prompt"] = "prompt"
    progress_message: str = ""
    content_length: int = 0
    source: SettingSource | Literal["builtin", "mcp", "plugin", "bundled"] = "builtin"
    arg_names: list[str] | None = None
    allowed_tools: list[str] | None = None
    model: str | None = None
    plugin_info: PluginInfo | None = None
    disable_non_interactive: bool = False
    hooks: Any | None = None  # HooksSettings
    skill_root: str | None = None
    context: Literal["inline", "fork"] = "inline"
    agent: str | None = None
    effort: EffortValue | None = None
    paths: list[str] | None = None
    get_prompt_for_command: Callable[[str, Any], Awaitable[list[dict[str, Any]]]] | None = None


# ============================================================================
# Local Command
# ============================================================================


@dataclass
class LocalCommandModule:
    """Module shape returned by load() for lazy-loaded local commands."""

    call: Callable[[str, Any], Awaitable[LocalCommandResult]] | None = None


@dataclass
class LocalCommand:
    """A local command that executes synchronously."""

    type: Literal["local"] = "local"
    supports_non_interactive: bool = False
    load: Callable[[], Awaitable[LocalCommandModule]] | None = None


# ============================================================================
# Local JSX Command
# ============================================================================


@dataclass
class LocalJSXCommandOnDoneOptions:
    """Options for command completion callback."""

    display: CommandResultDisplay = "user"
    should_query: bool = False
    meta_messages: list[str] | None = None
    next_input: str | None = None
    submit_next_input: bool = False


# Type for LocalJSXCommandOnDone callback
# Using Any for optional params to avoid Python version compatibility issues
LocalJSXCommandOnDone = Callable[..., None]


@dataclass
class LocalJSXCommandModule:
    """Module shape returned by load() for lazy-loaded JSX commands."""

    call: Callable[[LocalJSXCommandOnDone, Any, str], Awaitable[Any]] | None = None


@dataclass
class LocalJSXCommand:
    """A local JSX command that renders UI."""

    type: Literal["local-jsx"] = "local-jsx"
    load: Callable[[], Awaitable[LocalJSXCommandModule]] | None = None


# ============================================================================
# Command Base
# ============================================================================


@dataclass
class CommandBase:
    """Base properties for all command types."""

    name: str
    description: str
    availability: list[CommandAvailability] | None = None
    has_user_specified_description: bool = False
    is_enabled: Callable[[], bool] | None = None
    is_hidden: bool = False
    aliases: list[str] | None = None
    is_mcp: bool = False
    argument_hint: str | None = None
    when_to_use: str | None = None
    version: str | None = None
    disable_model_invocation: bool = False
    user_invocable: bool = True
    loaded_from: (
        Literal[
            "commands_DEPRECATED",
            "skills",
            "plugin",
            "managed",
            "bundled",
            "mcp",
        ]
        | None
    ) = None
    kind: Literal["workflow"] | None = None
    immediate: bool = False
    is_sensitive: bool = False
    user_facing_name: Callable[[], str] | None = None


@dataclass
class Command(CommandBase):
    """
    A complete command definition.

    Commands can be prompt commands, local commands, or local JSX commands.
    """

    # One of these will be set based on command type
    prompt_command: PromptCommand | None = None
    local_command: LocalCommand | None = None
    local_jsx_command: LocalJSXCommand | None = None


def get_command_name(cmd: CommandBase) -> str:
    """
    Resolve the user-visible name.

    Falls back to cmd.name when not overridden.
    """
    if cmd.user_facing_name:
        return cmd.user_facing_name()
    return cmd.name


def is_command_enabled(cmd: CommandBase) -> bool:
    """
    Resolve whether the command is enabled.

    Defaults to True if is_enabled is not set.
    """
    if cmd.is_enabled:
        return cmd.is_enabled()
    return True
