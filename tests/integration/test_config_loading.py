"""Integration tests for config and settings loading (real filesystem)."""

from __future__ import annotations

import json
from collections.abc import Generator
from pathlib import Path

import pytest

from claude_code.config.config import get_config_path, get_global_config, set_global_config
from claude_code.config.types import GlobalConfig
from claude_code.utils.settings.constants import reset_enabled_setting_sources
from claude_code.utils.settings.settings import (
    get_env_from_settings,
    get_merged_settings,
    reset_settings_cache,
)

pytestmark = pytest.mark.integration


@pytest.fixture(autouse=True)
def _reset_settings_state() -> Generator[None, None, None]:
    reset_settings_cache()
    reset_enabled_setting_sources()
    yield None
    reset_settings_cache()
    reset_enabled_setting_sources()


def test_get_global_config_reads_user_config_file(monkeypatch, tmp_path: Path) -> None:
    home = tmp_path / "claude_home"
    home.mkdir()
    cfg = home / "config.json"
    cfg.write_text(
        json.dumps(
            {
                "theme": "light",
                "verboseMode": True,
                "numStartups": 3,
            }
        ),
        encoding="utf-8",
    )
    monkeypatch.setenv("CLAUDE_CONFIG_DIR", str(home))
    # env_utils.get_claude_config_home_dir is cached
    from claude_code.utils import env_utils

    env_utils.get_claude_config_home_dir.cache_clear()
    from claude_code.utils import env

    if hasattr(env.get_global_claude_file, "cache_clear"):
        env.get_global_claude_file.cache_clear()

    try:
        gc = get_global_config()
        assert gc.theme == "light"
        assert gc.verbose_mode is True
        assert gc.num_startups == 3
    finally:
        env_utils.get_claude_config_home_dir.cache_clear()
        if hasattr(env.get_global_claude_file, "cache_clear"):
            env.get_global_claude_file.cache_clear()


def test_get_config_path_honors_claude_config_dir(monkeypatch, tmp_path: Path) -> None:
    home = tmp_path / "cfg"
    home.mkdir()
    monkeypatch.setenv("CLAUDE_CONFIG_DIR", str(home))
    from claude_code.utils import env_utils

    env_utils.get_claude_config_home_dir.cache_clear()
    try:
        p = get_config_path()
        assert p == str((home / "config.json").resolve())
    finally:
        env_utils.get_claude_config_home_dir.cache_clear()


def test_get_merged_settings_merges_user_and_project(monkeypatch, tmp_path: Path) -> None:
    home = tmp_path / "home"
    home.mkdir()
    user_file = home / "settings.json"
    user_file.write_text(
        json.dumps({"permissions": {"allow": ["Bash"], "deny": [], "ask": []}}),
        encoding="utf-8",
    )
    proj = tmp_path / "project"
    proj.mkdir()
    claude_dir = proj / ".claude"
    claude_dir.mkdir()
    (claude_dir / "settings.json").write_text(
        json.dumps({"permissions": {"allow": ["Read"], "deny": [], "ask": []}}),
        encoding="utf-8",
    )

    monkeypatch.setenv("CLAUDE_CONFIG_DIR", str(home))
    from claude_code.utils import env_utils

    env_utils.get_claude_config_home_dir.cache_clear()
    proj_root = str(proj.resolve())
    # settings.py binds get_cwd at import time; patch where it is used
    monkeypatch.setattr(
        "claude_code.utils.settings.settings.get_cwd",
        lambda: proj_root,
    )
    reset_settings_cache()

    try:
        merged = get_merged_settings()
        allow = merged.get("permissions", {}).get("allow", [])
        assert "Bash" in allow
        assert "Read" in allow
    finally:
        env_utils.get_claude_config_home_dir.cache_clear()
        reset_settings_cache()


def test_get_settings_for_source_user_file(monkeypatch, tmp_path: Path) -> None:
    home = tmp_path / "h"
    home.mkdir()
    (home / "settings.json").write_text(
        json.dumps({"env": {"INTEGRATION_FLAG": "1"}}),
        encoding="utf-8",
    )
    monkeypatch.setenv("CLAUDE_CONFIG_DIR", str(home))
    from claude_code.utils import env_utils

    env_utils.get_claude_config_home_dir.cache_clear()
    monkeypatch.setattr(
        "claude_code.utils.settings.settings.get_cwd",
        lambda: str(tmp_path.resolve()),
    )
    reset_settings_cache()
    try:
        env_map = get_env_from_settings("userSettings")
        assert env_map.get("INTEGRATION_FLAG") == "1"
    finally:
        env_utils.get_claude_config_home_dir.cache_clear()
        reset_settings_cache()


def test_environment_variable_claude_config_dir_visible(monkeypatch, tmp_path: Path) -> None:
    """Explicit override: CLAUDE_CONFIG_DIR must change resolved config home."""
    d = tmp_path / "alt"
    d.mkdir()
    monkeypatch.setenv("CLAUDE_CONFIG_DIR", str(d))
    from claude_code.utils import env_utils

    env_utils.get_claude_config_home_dir.cache_clear()
    try:
        assert env_utils.get_claude_config_home_dir() == str(d.resolve())
    finally:
        env_utils.get_claude_config_home_dir.cache_clear()


def test_set_global_config_roundtrip(monkeypatch, tmp_path: Path) -> None:
    home = tmp_path / "roundtrip"
    home.mkdir()
    monkeypatch.setenv("CLAUDE_CONFIG_DIR", str(home))
    from claude_code.utils import env_utils

    env_utils.get_claude_config_home_dir.cache_clear()
    try:
        cfg = GlobalConfig(theme="light", verbose_mode=True, num_startups=7, install_method="local")
        set_global_config(cfg)
        path = get_config_path()
        assert Path(path).is_file()
        loaded = get_global_config()
        assert loaded.theme == "light"
        assert loaded.verbose_mode is True
        assert loaded.num_startups == 7
        assert loaded.install_method == "local"
    finally:
        env_utils.get_claude_config_home_dir.cache_clear()


def test_set_global_config_preserves_mcp_servers(monkeypatch, tmp_path: Path) -> None:
    home = tmp_path / "mcpcfg"
    home.mkdir()
    monkeypatch.setenv("CLAUDE_CONFIG_DIR", str(home))
    from claude_code.utils import env_utils

    env_utils.get_claude_config_home_dir.cache_clear()
    try:
        cfg = GlobalConfig(mcp_servers={"local": {"type": "stdio", "command": "echo"}})
        set_global_config(cfg)
        loaded = get_global_config()
        assert "local" in loaded.mcp_servers
    finally:
        env_utils.get_claude_config_home_dir.cache_clear()
