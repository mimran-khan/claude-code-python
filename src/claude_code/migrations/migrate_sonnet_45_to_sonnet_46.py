"""
Migration: move Pro/Max/Team Premium 1P users off explicit Sonnet 4.5 strings.

Migrated from: migrations/migrateSonnet45ToSonnet46.ts
"""

from __future__ import annotations

import time
from dataclasses import dataclass

from claude_code.auth.helpers import (
    get_subscription_type,
    is_max_subscriber,
    is_team_premium_subscriber,
)
from claude_code.services.analytics.events import log_event
from claude_code.utils.config_utils import load_global_config_dict, save_global_config
from claude_code.utils.model.providers import get_api_provider
from claude_code.utils.settings.settings import get_settings_for_source, update_settings_for_source


@dataclass(frozen=True)
class MigrateSonnet45ToSonnet46Spec:
    """Explicit Sonnet 4.5 settings eligible for alias upgrade."""

    source_ts: str = "migrateSonnet45ToSonnet46.ts"
    legacy_models: tuple[str, ...] = (
        "claude-sonnet-4-5-20250929",
        "claude-sonnet-4-5-20250929[1m]",
        "sonnet-4-5-20250929",
        "sonnet-4-5-20250929[1m]",
    )


def _is_target_subscriber() -> bool:
    if get_subscription_type() == "pro":
        return True
    if is_max_subscriber():
        return True
    return bool(is_team_premium_subscriber())


def migrate_sonnet_45_to_sonnet_46() -> None:
    if get_api_provider() != "firstParty":
        return
    if not _is_target_subscriber():
        return

    model = (get_settings_for_source("userSettings") or {}).get("model")
    if not isinstance(model, str) or model not in MigrateSonnet45ToSonnet46Spec.legacy_models:
        return

    has_1m = model.endswith("[1m]")
    update_settings_for_source(
        "userSettings",
        {"model": "sonnet[1m]" if has_1m else "sonnet"},
    )

    cfg = load_global_config_dict()
    if cfg.get("numStartups", 0) > 1:
        save_global_config(
            lambda c: {**c, "sonnet45To46MigrationTimestamp": int(time.time() * 1000)},
        )

    log_event(
        "tengu_sonnet45_to_46_migration",
        {"from_model": model, "has_1m": has_1m},
    )
