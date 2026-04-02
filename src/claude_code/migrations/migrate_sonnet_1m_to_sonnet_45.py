"""
Migration: pin ``sonnet[1m]`` users to explicit Sonnet 4.5 1M ID.

Migrated from: migrations/migrateSonnet1mToSonnet45.ts
"""

from __future__ import annotations

from dataclasses import dataclass

from claude_code.bootstrap.state import get_main_loop_model_override, set_main_loop_model_override
from claude_code.utils.config_utils import load_global_config_dict, save_global_config
from claude_code.utils.settings.settings import get_settings_for_source, update_settings_for_source


@dataclass(frozen=True)
class MigrateSonnet1mToSonnet45Spec:
    """Pinned explicit model for former ``sonnet[1m]`` users."""

    source_ts: str = "migrateSonnet1mToSonnet45.ts"
    target_model: str = "sonnet-4-5-20250929[1m]"
    completion_flag: str = "sonnet1m45MigrationComplete"


def migrate_sonnet_1m_to_sonnet_45() -> None:
    raw = load_global_config_dict()
    if raw.get(MigrateSonnet1mToSonnet45Spec.completion_flag):
        return

    model = (get_settings_for_source("userSettings") or {}).get("model")
    if model == "sonnet[1m]":
        update_settings_for_source(
            "userSettings",
            {"model": MigrateSonnet1mToSonnet45Spec.target_model},
        )

    override = get_main_loop_model_override()
    if override == "sonnet[1m]":
        set_main_loop_model_override(MigrateSonnet1mToSonnet45Spec.target_model)

    save_global_config(
        lambda c: {**c, MigrateSonnet1mToSonnet45Spec.completion_flag: True},
    )
