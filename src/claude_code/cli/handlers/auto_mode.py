"""Auto-mode CLI. Migrated from: cli/handlers/autoMode.ts."""

from __future__ import annotations

import json
import sys
from typing import Any

# External defaults mirror TS getDefaultExternalAutoModeRules shape.
_DEFAULT_RULES: dict[str, list[str]] = {
    "allow": [],
    "soft_deny": [],
    "environment": [],
}


def auto_mode_defaults_handler() -> None:
    sys.stdout.write(json.dumps(_DEFAULT_RULES, indent=2) + "\n")


def auto_mode_config_handler() -> None:
    sys.stdout.write(json.dumps(_DEFAULT_RULES, indent=2) + "\n")


async def auto_mode_critique_handler(options: dict[str, Any] | None = None) -> None:
    _ = options
    sys.stdout.write(
        "No custom auto mode rules in Python settings yet.\nAdd rules under settings autoMode and re-run.\n"
    )
