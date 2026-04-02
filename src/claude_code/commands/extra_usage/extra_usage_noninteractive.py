"""Migrated from: commands/extra-usage/extra-usage-noninteractive.ts"""

from __future__ import annotations

from .extra_usage_core import run_extra_usage


async def call() -> dict[str, str]:
    result = await run_extra_usage()
    if result.type == "message":
        return {"type": "text", "value": result.value}
    return {
        "type": "text",
        "value": (
            f"Browser opened to manage extra usage. If it didn't open, visit: {result.url}"
            if result.opened
            else f"Please visit {result.url} to manage extra usage."
        ),
    }
