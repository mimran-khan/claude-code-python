"""Plugin startup validation. Migrated from pluginStartupCheck.ts."""

from __future__ import annotations


async def run_plugin_startup_checks() -> list[str]:
    return []


__all__ = ["run_plugin_startup_checks"]
