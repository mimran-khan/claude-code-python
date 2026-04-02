"""Additional unit tests for claude_code.utils.env."""

from __future__ import annotations

import os
from unittest.mock import patch

import pytest

from claude_code.utils import env as env_mod
from claude_code.utils.env import (
    detect_terminal,
    getenv_with_default,
    is_ci_environment,
    is_command_available,
    load_dotenv_for_project,
    merge_env_with_defaults,
)


def test_merge_env_with_defaults_explicit_wins() -> None:
    assert merge_env_with_defaults({"A": "new"}, {"A": "old", "B": "1"}) == {
        "A": "new",
        "B": "1",
    }


def test_getenv_with_default_uses_env(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("ENV_MORE_XYZ", "from_env")
    assert getenv_with_default("ENV_MORE_XYZ", "d") == "from_env"


def test_getenv_with_default_falls_back(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.delenv("ENV_MORE_MISSING", raising=False)
    assert getenv_with_default("ENV_MORE_MISSING", "fallback") == "fallback"


def test_load_dotenv_for_project_loads_closest(tmp_path, monkeypatch: pytest.MonkeyPatch) -> None:
    root = tmp_path / "proj"
    root.mkdir()
    (root / ".env").write_text("DOTENV_PROJ_A=1\n", encoding="utf-8")
    (root / ".env.local").write_text("DOTENV_PROJ_B=2\n", encoding="utf-8")
    monkeypatch.delenv("DOTENV_PROJ_A", raising=False)
    monkeypatch.delenv("DOTENV_PROJ_B", raising=False)
    loaded = load_dotenv_for_project(str(root), filenames=(".env", ".env.local"))
    assert any(str(root / ".env") == p for p in loaded)
    assert os.environ.get("DOTENV_PROJ_A") == "1"
    assert os.environ.get("DOTENV_PROJ_B") == "2"


def test_detect_terminal_cursor_trace(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("CURSOR_TRACE_ID", "t1")
    monkeypatch.delenv("VSCODE_GIT_ASKPASS_MAIN", raising=False)
    assert detect_terminal() == "cursor"


def test_detect_terminal_vscode_term_program(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.delenv("CURSOR_TRACE_ID", raising=False)
    monkeypatch.delenv("VSCODE_GIT_ASKPASS_MAIN", raising=False)
    monkeypatch.delenv("__CFBundleIdentifier", raising=False)
    monkeypatch.setenv("TERM_PROGRAM", "vscode")
    assert detect_terminal() == "vscode"


def test_is_ci_environment_true_when_ci_set(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("CI", "true")
    assert is_ci_environment() is True


def test_is_ci_environment_false_when_unset(monkeypatch: pytest.MonkeyPatch) -> None:
    for v in ("CI", "CONTINUOUS_INTEGRATION", "GITHUB_ACTIONS", "GITLAB_CI", "JENKINS_URL"):
        monkeypatch.delenv(v, raising=False)
    assert is_ci_environment() is False


@patch("claude_code.utils.env.shutil.which")
def test_is_command_available_delegates_to_which(mock_which) -> None:
    mock_which.return_value = "/usr/bin/python3"
    assert is_command_available("python3") is True
    mock_which.return_value = None
    assert is_command_available("no-such-cmd-xyz") is False


def test_get_global_claude_file_prefers_legacy_json(tmp_path, monkeypatch: pytest.MonkeyPatch) -> None:
    env_mod.get_global_claude_file.cache_clear()
    cfg = tmp_path / "cfg"
    cfg.mkdir()
    legacy = cfg / ".config.json"
    legacy.write_text("{}", encoding="utf-8")
    monkeypatch.setenv("CLAUDE_CONFIG_DIR", str(cfg))
    try:
        p = env_mod.get_global_claude_file()
        assert p == str(legacy)
    finally:
        env_mod.get_global_claude_file.cache_clear()
