"""
Migration: mark Pro / first-party default model transition (notification bookkeeping).

Migrated from: migrations/resetProToOpusDefault.ts
"""

from __future__ import annotations

import time
from dataclasses import dataclass

from claude_code.auth.helpers import get_subscription_type
from claude_code.services.analytics.events import log_event
from claude_code.utils.config_utils import load_global_config_dict, save_global_config
from claude_code.utils.model.providers import get_api_provider
from claude_code.utils.settings.settings import get_merged_settings


@dataclass(frozen=True)
class ResetProToOpusDefaultSpec:
    """Global config keys for Pro → Opus default rollout."""

    source_ts: str = "resetProToOpusDefault.ts"
    complete_key: str = "opusProMigrationComplete"
    timestamp_key: str = "opusProMigrationTimestamp"


def reset_pro_to_opus_default() -> None:
    raw = load_global_config_dict()
    if raw.get(ResetProToOpusDefaultSpec.complete_key):
        return

    api_provider = get_api_provider()

    if api_provider != "firstParty" or get_subscription_type() != "pro":
        save_global_config(
            lambda c: {**c, ResetProToOpusDefaultSpec.complete_key: True},
        )
        log_event("tengu_reset_pro_to_opus_default", {"skipped": True})
        return

    settings = get_merged_settings()
    had_custom_model = settings.get("model") is not None

    if not had_custom_model:
        ts = int(time.time() * 1000)
        save_global_config(
            lambda c: {
                **c,
                ResetProToOpusDefaultSpec.complete_key: True,
                ResetProToOpusDefaultSpec.timestamp_key: ts,
            },
        )
        log_event(
            "tengu_reset_pro_to_opus_default",
            {"skipped": False, "had_custom_model": False},
        )
    else:
        save_global_config(
            lambda c: {**c, ResetProToOpusDefaultSpec.complete_key: True},
        )
        log_event(
            "tengu_reset_pro_to_opus_default",
            {"skipped": False, "had_custom_model": True},
        )
