"""Unit tests for TypeScript-parity migrations."""

from __future__ import annotations

import json
from pathlib import Path

import pytest

from claude_code.migrations.migrate_repl_bridge_enabled_to_remote_control_at_startup import (
    migrate_repl_bridge_enabled_to_remote_control_at_startup,
)
from claude_code.migrations.records import MIGRATION_SOURCE_RECORDS
from claude_code.migrations.startup import CURRENT_MIGRATION_VERSION, run_sync_migrations
from claude_code.migrations.version_compare import (
    MigrationVersion,
    version_strings_gte,
    version_tuple_from_string,
    version_tuple_gte,
)
from claude_code.utils.config_utils import clear_config_cache
from claude_code.utils.model.model import parse_user_specified_model


def test_migration_source_records_covers_all_ts_migrations() -> None:
    ts_names = {r.ts_file for r in MIGRATION_SOURCE_RECORDS}
    expected = {
        "migrateAutoUpdatesToSettings.ts",
        "migrateBypassPermissionsAcceptedToSettings.ts",
        "migrateEnableAllProjectMcpServersToSettings.ts",
        "migrateFennecToOpus.ts",
        "migrateLegacyOpusToCurrent.ts",
        "migrateOpusToOpus1m.ts",
        "migrateReplBridgeEnabledToRemoteControlAtStartup.ts",
        "migrateSonnet1mToSonnet45.ts",
        "migrateSonnet45ToSonnet46.ts",
        "resetAutoModeOptInForDefaultOffer.ts",
        "resetProToOpusDefault.ts",
    }
    assert ts_names == expected


def test_version_tuple_from_string_parses_segments() -> None:
    assert version_tuple_from_string("1.2.3") == (1, 2, 3)
    assert version_tuple_from_string("no-digits") == (0,)


def test_version_tuple_gte_lexicographic() -> None:
    assert version_tuple_gte((2, 0), (1, 99)) is True
    assert version_tuple_gte((1,), (1, 0)) is True


def test_version_strings_gte() -> None:
    assert version_strings_gte("2.0", "1.9") is True


def test_migration_version_compare() -> None:
    assert MigrationVersion(11) == MigrationVersion(11)
    assert MigrationVersion(10) < MigrationVersion(11)


def test_run_sync_migrations_sets_migration_version(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path
) -> None:
    cfg_path = tmp_path / "config.json"
    cfg_path.write_text("{}", encoding="utf-8")
    monkeypatch.setenv("CLAUDE_CONFIG_DIR", str(tmp_path))
    clear_config_cache()

    run_sync_migrations()

    data = json.loads(cfg_path.read_text(encoding="utf-8"))
    assert data.get("migrationVersion") == CURRENT_MIGRATION_VERSION


def test_run_sync_migrations_idempotent_when_version_current(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path
) -> None:
    cfg_path = tmp_path / "config.json"
    cfg_path.write_text(
        json.dumps({"migrationVersion": CURRENT_MIGRATION_VERSION, "x": 1}),
        encoding="utf-8",
    )
    monkeypatch.setenv("CLAUDE_CONFIG_DIR", str(tmp_path))
    clear_config_cache()

    run_sync_migrations()

    data = json.loads(cfg_path.read_text(encoding="utf-8"))
    assert data.get("x") == 1
    assert data.get("migrationVersion") == CURRENT_MIGRATION_VERSION


def test_parse_user_specified_model_1m_alias_suffix() -> None:
    out = parse_user_specified_model("opus[1m]")
    assert out.endswith("[1m]")
    assert "opus" in out.lower()


def test_migrate_repl_bridge_copies_boolean(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path
) -> None:
    cfg_path = tmp_path / "config.json"
    cfg_path.write_text(
        json.dumps({"replBridgeEnabled": True, "other": 1}),
        encoding="utf-8",
    )
    monkeypatch.setenv("CLAUDE_CONFIG_DIR", str(tmp_path))
    clear_config_cache()

    migrate_repl_bridge_enabled_to_remote_control_at_startup()

    data = json.loads(cfg_path.read_text(encoding="utf-8"))
    assert data.get("remoteControlAtStartup") is True
    assert "replBridgeEnabled" not in data
    assert data.get("other") == 1


def test_migrate_repl_bridge_idempotent_when_new_key_set(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path
) -> None:
    cfg_path = tmp_path / "config.json"
    cfg_path.write_text(
        json.dumps({"replBridgeEnabled": False, "remoteControlAtStartup": True}),
        encoding="utf-8",
    )
    monkeypatch.setenv("CLAUDE_CONFIG_DIR", str(tmp_path))
    clear_config_cache()

    migrate_repl_bridge_enabled_to_remote_control_at_startup()

    data = json.loads(cfg_path.read_text(encoding="utf-8"))
    assert data.get("remoteControlAtStartup") is True
    assert "replBridgeEnabled" in data
