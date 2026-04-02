"""
Migrated from: commands/plugin/parseArgs.ts
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Literal


@dataclass(frozen=True)
class ParsedMenu:
    type: Literal["menu"] = "menu"


@dataclass(frozen=True)
class ParsedHelp:
    type: Literal["help"] = "help"


@dataclass(frozen=True)
class ParsedInstall:
    type: Literal["install"] = "install"
    marketplace: str | None = None
    plugin: str | None = None


@dataclass(frozen=True)
class ParsedManage:
    type: Literal["manage"] = "manage"


@dataclass(frozen=True)
class ParsedUninstall:
    type: Literal["uninstall"] = "uninstall"
    plugin: str | None = None


@dataclass(frozen=True)
class ParsedEnable:
    type: Literal["enable"] = "enable"
    plugin: str | None = None


@dataclass(frozen=True)
class ParsedDisable:
    type: Literal["disable"] = "disable"
    plugin: str | None = None


@dataclass(frozen=True)
class ParsedValidate:
    type: Literal["validate"] = "validate"
    path: str | None = None


@dataclass(frozen=True)
class ParsedMarketplace:
    type: Literal["marketplace"] = "marketplace"
    action: Literal["add", "remove", "update", "list"] | None = None
    target: str | None = None


ParsedCommand = (
    ParsedMenu
    | ParsedHelp
    | ParsedInstall
    | ParsedManage
    | ParsedUninstall
    | ParsedEnable
    | ParsedDisable
    | ParsedValidate
    | ParsedMarketplace
)


def parse_plugin_args(args: str | None) -> ParsedCommand:
    if not args:
        return ParsedMenu()

    parts = args.strip().split()
    command = parts[0].lower() if parts else ""

    if command in ("help", "--help", "-h"):
        return ParsedHelp()

    if command in ("install", "i"):
        target = parts[1] if len(parts) > 1 else None
        if not target:
            return ParsedInstall()
        if "@" in target:
            plugin, _, marketplace = target.partition("@")
            return ParsedInstall(plugin=plugin or None, marketplace=marketplace or None)
        is_marketplace = (
            target.startswith("http://")
            or target.startswith("https://")
            or target.startswith("file://")
            or "/" in target
            or "\\" in target
        )
        if is_marketplace:
            return ParsedInstall(marketplace=target)
        return ParsedInstall(plugin=target)

    if command == "manage":
        return ParsedManage()

    if command == "uninstall":
        return ParsedUninstall(plugin=parts[1] if len(parts) > 1 else None)

    if command == "enable":
        return ParsedEnable(plugin=parts[1] if len(parts) > 1 else None)

    if command == "disable":
        return ParsedDisable(plugin=parts[1] if len(parts) > 1 else None)

    if command == "validate":
        rest = " ".join(parts[1:]).strip()
        return ParsedValidate(path=rest or None)

    if command in ("marketplace", "market"):
        action = parts[1].lower() if len(parts) > 1 else None
        target = " ".join(parts[2:]) if len(parts) > 2 else ""
        if action == "add":
            return ParsedMarketplace(action="add", target=target or None)
        if action in ("remove", "rm"):
            return ParsedMarketplace(action="remove", target=target or None)
        if action == "update":
            return ParsedMarketplace(action="update", target=target or None)
        if action == "list":
            return ParsedMarketplace(action="list")
        return ParsedMarketplace()

    return ParsedMenu()
