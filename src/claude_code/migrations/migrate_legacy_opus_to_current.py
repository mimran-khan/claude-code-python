"""
Migration: move first-party users off explicit Opus 4.0/4.1 strings to ``opus`` alias.

Migrated from: migrations/migrateLegacyOpusToCurrent.ts
"""

from __future__ import annotations

import time
from dataclasses import dataclass

from claude_code.services.analytics.events import log_event
from claude_code.utils.config_utils import save_global_config
from claude_code.utils.model.model import is_legacy_model_remap_enabled
from claude_code.utils.model.providers import get_api_provider
from claude_code.utils.settings.settings import get_settings_for_source, update_settings_for_source


@dataclass(frozen=True)
class MigrateLegacyOpusSpec:
    """Explicit legacy Opus IDs eligible for cleanup."""

    source_ts: str = "migrateLegacyOpusToCurrent.ts"
    legacy_models: tuple[str, ...] = (
        "claude-opus-4-20250514",
        "claude-opus-4-1-20250805",
        "claude-opus-4-0",
        "claude-opus-4-1",
    )


def migrate_legacy_opus_to_current() -> None:
    if get_api_provider() != "firstParty":
        return
    if not is_legacy_model_remap_enabled():
        return

    model = (get_settings_for_source("userSettings") or {}).get("model")
    if model not in MigrateLegacyOpusSpec.legacy_models:
        return

    update_settings_for_source("userSettings", {"model": "opus"})
    save_global_config(
        lambda c: {**c, "legacyOpusMigrationTimestamp": int(time.time() * 1000)},
    )
    log_event("tengu_legacy_opus_migration", {"from_model": str(model)})
