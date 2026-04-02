"""
Command specification dataclasses (TypeScript Command shape).

Migrated from: types/command.ts (metadata fields used by commands/*.ts)
"""

from __future__ import annotations

from collections.abc import Awaitable, Callable
from dataclasses import dataclass
from typing import Any, Literal

CommandTypeLiteral = Literal["local", "local-jsx", "prompt"]
AvailabilityLiteral = Literal["claude-ai", "console"]
CommandSourceLiteral = Literal["builtin", "plugin", "bundled", "mcp", "skills"]

# Local command return shape (text channel)
LocalTextResult = dict[str, Any]


@dataclass(frozen=True)
class CommandSpec:
    """
    Static slash-command registration record.

    Dynamic getters from TypeScript (`get isHidden`, `get description`, …)
    are represented as optional callables evaluated at registration time.

    ``load_symbol`` is a dotted import path for :func:`importlib.import_module`
    (for example ``claude_code.commands.rename.ui``), not a parent module plus a
    runtime attribute. Lazy UI / handler modules must exist as ``.py`` files.
    """

    type: CommandTypeLiteral
    name: str
    description: str
    aliases: tuple[str, ...] = ()
    argument_hint: str | None = None
    supports_non_interactive: bool = False
    immediate: bool = False
    hidden: bool = False
    source: CommandSourceLiteral = "builtin"
    availability: tuple[AvailabilityLiteral, ...] | None = None
    allowed_tools: tuple[str, ...] = ()
    progress_message: str | None = None
    content_length: int | None = None
    load_symbol: str | None = None
    is_enabled: Callable[[], bool] | None = None
    is_hidden_fn: Callable[[], bool] | None = None
    immediate_fn: Callable[[], bool] | None = None
    description_fn: Callable[[], str] | None = None
    content_length_fn: Callable[[], int] | None = None


def resolve_description(spec: CommandSpec) -> str:
    if spec.description_fn is not None:
        return spec.description_fn()
    return spec.description


def resolve_hidden(spec: CommandSpec) -> bool:
    if spec.hidden:
        return True
    if spec.is_hidden_fn is not None:
        return spec.is_hidden_fn()
    return False


def resolve_immediate(spec: CommandSpec) -> bool:
    if spec.immediate_fn is not None:
        return spec.immediate_fn()
    return spec.immediate


def resolve_enabled(spec: CommandSpec) -> bool:
    if spec.is_enabled is None:
        return True
    return spec.is_enabled()


# Optional hooks for prompt-type commands
GetPromptForCommand = Callable[..., Awaitable[list[dict[str, Any]]]]


@dataclass
class PromptCommandBundle:
    """Runnable prompt command: metadata + prompt builder."""

    spec: CommandSpec
    get_prompt_for_command: GetPromptForCommand
