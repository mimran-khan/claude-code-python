"""Shared command spec dataclasses (utils/bash/registry.ts)."""

from __future__ import annotations

from dataclasses import dataclass, field


@dataclass
class Argument:
    name: str | None = None
    description: str | None = None
    is_dangerous: bool = False
    is_variadic: bool = False
    is_optional: bool = False
    is_command: bool = False
    is_module: str | bool | None = None
    is_script: bool = False


@dataclass
class Option:
    name: str | list[str]
    description: str | None = None
    args: list[Argument] | Argument | None = None
    is_required: bool = False


@dataclass
class CommandSpec:
    name: str
    description: str | None = None
    subcommands: list[CommandSpec] = field(default_factory=list)
    args: list[Argument] | Argument | None = None
    options: list[Option] = field(default_factory=list)
