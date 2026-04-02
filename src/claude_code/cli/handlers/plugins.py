"""Plugin / marketplace CLI. Migrated from: cli/handlers/plugins.ts (stubs + registry)."""

from __future__ import annotations

import json
from typing import Any

from ...plugins.loader import discover_plugins
from ..exit import cli_error, cli_ok

VALID_INSTALLABLE_SCOPES = ("user", "project", "local")
VALID_UPDATE_SCOPES = ("user", "project", "local", "managed")


def handle_marketplace_error(error: BaseException, action: str) -> None:
    cli_error(f"Failed to {action}: {error}")


async def plugin_validate_handler(
    manifest_path: str,
    options: dict[str, Any] | None = None,
) -> None:
    _ = options
    cli_ok(f"Validate manifest at {manifest_path} (wire validate_manifest).")


async def plugin_list_handler(options: dict[str, Any] | None = None) -> None:
    options = options or {}
    plugins = discover_plugins()
    rows = [{"name": p.name, "path": str(p.path)} for p in plugins]
    if options.get("json"):
        cli_ok(json.dumps(rows, indent=2))
    if not rows:
        cli_ok("No plugins discovered.")
    print("Plugins:\n")
    for r in rows:
        print(f"  - {r['id']} ({r['name']}): {r['path']}")
    cli_ok()


async def marketplace_add_handler(source: str, options: dict[str, Any] | None = None) -> None:
    _ = source, options
    cli_ok("Marketplace add (wire marketplaceManager).")


async def marketplace_list_handler(options: dict[str, Any] | None = None) -> None:
    if options and options.get("json"):
        cli_ok(json.dumps([], indent=2))
    cli_ok("No marketplaces configured")


async def marketplace_remove_handler(name: str, options: dict[str, Any] | None = None) -> None:
    _ = name, options
    cli_ok(f"Removed marketplace {name} (stub).")


async def marketplace_update_handler(
    name: str | None,
    options: dict[str, Any] | None = None,
) -> None:
    _ = name, options
    cli_ok("Marketplace update (stub).")


async def plugin_install_handler(plugin: str, options: dict[str, Any] | None = None) -> None:
    _ = options
    print(f"Install plugin {plugin} (stub).")


async def plugin_uninstall_handler(plugin: str, options: dict[str, Any] | None = None) -> None:
    _ = options
    print(f"Uninstall plugin {plugin} (stub).")


async def plugin_enable_handler(plugin: str, options: dict[str, Any] | None = None) -> None:
    _ = options
    print(f"Enable plugin {plugin} (stub).")


async def plugin_disable_handler(
    plugin: str | None,
    options: dict[str, Any] | None = None,
) -> None:
    _ = plugin, options
    print("Disable plugin(s) (stub).")


async def plugin_update_handler(plugin: str, options: dict[str, Any] | None = None) -> None:
    _ = options
    print(f"Update plugin {plugin} (stub).")
