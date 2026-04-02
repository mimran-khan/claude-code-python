"""Migrated from: commands/extra-usage/extra-usage-core.ts"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Literal


@dataclass(frozen=True)
class ExtraUsageMessage:
    type: Literal["message"] = "message"
    value: str = ""


@dataclass(frozen=True)
class ExtraUsageBrowser:
    type: Literal["browser-opened"] = "browser-opened"
    url: str = ""
    opened: bool = False


ExtraUsageResult = ExtraUsageMessage | ExtraUsageBrowser


async def run_extra_usage() -> ExtraUsageResult:
    """Orchestrate extra-usage flow; wire billing APIs when ported."""
    return ExtraUsageMessage(value="Extra usage configuration is not fully wired in this Python build.")
