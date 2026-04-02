"""
Migrated from: commands/install-slack-app/install-slack-app.ts
"""

from __future__ import annotations

import asyncio
from collections.abc import Awaitable, Callable, Mapping
from dataclasses import dataclass
from typing import Any

SLACK_APP_URL = "https://slack.com/marketplace/A08SF47R6P4-claude"


@dataclass
class LocalTextResult:
    """Mirrors LocalCommandResult type: { type: 'text', value: string }."""

    type: str = "text"
    value: str = ""


async def call(
    open_browser: Callable[[str], bool | Awaitable[bool]] | None = None,
    log_event: Callable[[str, Mapping[str, Any]], None] | None = None,
    save_global_config: Callable[
        [Callable[[dict[str, Any]], dict[str, Any]]],
        None,
    ]
    | None = None,
) -> LocalTextResult:
    if log_event is not None:
        log_event("tengu_install_slack_app_clicked", {})

    if save_global_config is not None:

        def _bump(current: dict[str, Any]) -> dict[str, Any]:
            return {
                **current,
                "slack_app_install_count": (current.get("slack_app_install_count") or 0) + 1,
            }

        save_global_config(_bump)

    if open_browser is None:
        return LocalTextResult(
            value=f"Open Slack app installation page: {SLACK_APP_URL}",
        )

    maybe = open_browser(SLACK_APP_URL)
    success = bool(await maybe) if asyncio.iscoroutine(maybe) else bool(maybe)

    if success:
        return LocalTextResult(value="Opening Slack app installation page in browser…")
    return LocalTextResult(
        value=f"Couldn't open browser. Visit: {SLACK_APP_URL}",
    )
