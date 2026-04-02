"""Unit tests for ``claude_code.utils.config_utils``."""

from __future__ import annotations

import json
from pathlib import Path
from unittest.mock import patch

import pytest

from claude_code.utils.config_utils import (
    GlobalConfig,
    apply_defaults,
    clear_config_cache,
    get_api_key,
    get_claude_config_dir,
    get_global_config,
    get_global_config_path,
    get_memory_path,
    get_model,
    get_project_config,
    get_project_config_path,
    load_global_config_dict,
    load_json_config,
    merge_settings,
    save_global_config,
    save_project_config,
)
from claude_code.utils.errors import ConfigParseError


@pytest.fixture(autouse=True)
def _clear_cfg() -> None:
    clear_config_cache()
    yield
    clear_config_cache()


def test_get_claude_config_dir_env_override(monkeypatch: pytest.MonkeyPatch, tmp_path) -> None:
    monkeypatch.setenv("CLAUDE_CONFIG_DIR", str(tmp_path))
    assert get_claude_config_dir() == str(tmp_path)


def test_get_global_config_path_joins_config_json(monkeypatch: pytest.MonkeyPatch, tmp_path) -> None:
    monkeypatch.setenv("CLAUDE_CONFIG_DIR", str(tmp_path))
    assert get_global_config_path() == str(tmp_path / "config.json")


def test_get_project_config_path_explicit(tmp_path) -> None:
    p = get_project_config_path(str(tmp_path / "proj"))
    assert p.endswith(".claude/config.json")


def test_load_global_config_dict_missing_returns_empty(tmp_path, monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("CLAUDE_CONFIG_DIR", str(tmp_path))
    assert load_global_config_dict() == {}


def test_load_global_config_dict_invalid_json_returns_empty(tmp_path, monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("CLAUDE_CONFIG_DIR", str(tmp_path))
    cfg = tmp_path / "config.json"
    cfg.write_text("{", encoding="utf-8")
    assert load_global_config_dict() == {}


def test_get_global_config_creates_default_when_missing(tmp_path, monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("CLAUDE_CONFIG_DIR", str(tmp_path))
    g = get_global_config()
    assert isinstance(g, GlobalConfig)
    assert g.theme == "dark"


def test_get_global_config_invalid_json_raises(tmp_path, monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("CLAUDE_CONFIG_DIR", str(tmp_path))
    (tmp_path / "config.json").write_text("not-json", encoding="utf-8")
    with pytest.raises(ConfigParseError):
        get_global_config()


def test_get_global_config_handles_open_error(tmp_path, monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("CLAUDE_CONFIG_DIR", str(tmp_path))
    with patch("claude_code.utils.config_utils.os.path.exists", return_value=True):
        with patch("builtins.open", side_effect=OSError("denied")):
            g = get_global_config()
    assert isinstance(g, GlobalConfig)


def test_save_global_config_writes_and_clears_cache(tmp_path, monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("CLAUDE_CONFIG_DIR", str(tmp_path))
    _ = get_global_config()
    save_global_config(lambda d: {**d, "numStartups": 5})
    data = json.loads((tmp_path / "config.json").read_text(encoding="utf-8"))
    assert data["numStartups"] == 5
    g2 = get_global_config()
    assert g2.num_startups == 5


def test_get_project_config_from_file(tmp_path) -> None:
    cfg_dir = tmp_path / ".claude"
    cfg_dir.mkdir()
    (cfg_dir / "config.json").write_text(
        json.dumps({"allowedTools": ["Bash"], "lastSessionId": "s1"}),
        encoding="utf-8",
    )
    pc = get_project_config(str(tmp_path))
    assert "Bash" in pc.allowed_tools
    assert pc.last_session_id == "s1"


def test_save_project_config_updates_disk(tmp_path) -> None:
    save_project_config(str(tmp_path), lambda d: {**d, "allowedTools": ["Read"]})
    path = Path(get_project_config_path(str(tmp_path)))
    assert path.read_text(encoding="utf-8")
    data = json.loads(path.read_text(encoding="utf-8"))
    assert data["allowedTools"] == ["Read"]


def test_get_memory_path_suffix(monkeypatch: pytest.MonkeyPatch, tmp_path) -> None:
    monkeypatch.setenv("CLAUDE_CONFIG_DIR", str(tmp_path))
    assert get_memory_path() == str(tmp_path / "memory")


def test_get_api_key_prefers_env(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("ANTHROPIC_API_KEY", "env-key")
    assert get_api_key() == "env-key"


def test_get_model_prefers_env(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("CLAUDE_CODE_MODEL", "custom-model")
    assert get_model() == "custom-model"


def test_get_model_default_when_unset(monkeypatch: pytest.MonkeyPatch, tmp_path) -> None:
    monkeypatch.delenv("CLAUDE_CODE_MODEL", raising=False)
    monkeypatch.setenv("CLAUDE_CONFIG_DIR", str(tmp_path))
    assert get_model() == "claude-sonnet-4-20250514"


def test_load_json_config_success(tmp_path) -> None:
    p = tmp_path / "x.json"
    p.write_text('{"a": 1}', encoding="utf-8")
    assert load_json_config(p) == {"a": 1}


def test_load_json_config_not_dict_raises(tmp_path) -> None:
    p = tmp_path / "a.json"
    p.write_text("[1,2]", encoding="utf-8")
    with pytest.raises(ConfigParseError):
        load_json_config(p)


def test_merge_settings_delegates_deep_merge() -> None:
    with patch("claude_code.utils.json_utils.deep_merge", return_value={"k": "v"}) as dm:
        out = merge_settings({"a": 1}, {"b": 2})
    dm.assert_called_once()
    assert out == {"k": "v"}


def test_apply_defaults_order() -> None:
    with patch("claude_code.utils.json_utils.deep_merge", return_value={"merged": True}) as dm:
        out = apply_defaults({"x": 1}, {"y": 2})
    dm.assert_called_once()
    assert out == {"merged": True}


def test_parse_global_config_oauth_non_dict_dropped(tmp_path, monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("CLAUDE_CONFIG_DIR", str(tmp_path))
    (tmp_path / "config.json").write_text(
        json.dumps({"oauthAccount": "not-a-dict", "numStartups": 2}),
        encoding="utf-8",
    )
    g = get_global_config()
    assert g.oauth_account is None
    assert g.num_startups == 2


def test_get_project_config_empty_json_uses_defaults(tmp_path) -> None:
    cfg_dir = tmp_path / ".claude"
    cfg_dir.mkdir()
    (cfg_dir / "config.json").write_text("{}", encoding="utf-8")
    pc = get_project_config(str(tmp_path))
    assert pc.allowed_tools == []
