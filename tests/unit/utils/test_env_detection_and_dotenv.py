"""Unit tests for ``claude_code.utils.env`` (detection, dotenv, platform)."""

from __future__ import annotations

from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest

from claude_code.utils import env as env_mod
from claude_code.utils import env_utils
from claude_code.utils.env import (
    detect_editor_from_env,
    detect_package_managers,
    detect_runtimes,
    detect_terminal,
    find_dotenv_file,
    get_global_claude_file,
    get_hostname,
    get_platform,
    get_shell,
    get_terminal_columns,
    get_terminal_rows,
    has_internet_access,
    is_conductor,
    is_darwin,
    is_docker,
    is_interactive_shell,
    is_linux,
    is_windows,
    is_wsl_environment,
    load_dotenv_file,
)


@pytest.fixture(autouse=True)
def _clear_env_caches() -> None:
    env_mod.get_global_claude_file.cache_clear()
    env_mod.has_internet_access.cache_clear()
    env_mod.detect_package_managers.cache_clear()
    env_mod.detect_runtimes.cache_clear()
    env_mod.is_wsl_environment.cache_clear()
    env_mod.get_platform.cache_clear()
    env_mod.get_hostname.cache_clear()
    env_utils.get_claude_config_home_dir.cache_clear()
    yield
    env_mod.get_global_claude_file.cache_clear()
    env_mod.has_internet_access.cache_clear()
    env_mod.detect_package_managers.cache_clear()
    env_mod.detect_runtimes.cache_clear()
    env_mod.is_wsl_environment.cache_clear()
    env_mod.get_platform.cache_clear()
    env_mod.get_hostname.cache_clear()
    env_utils.get_claude_config_home_dir.cache_clear()


@patch("claude_code.utils.env.get_claude_config_home_dir")
@patch("claude_code.utils.env.os.path.exists")
def test_get_global_claude_file_prefers_legacy_config_json(
    mock_exists: MagicMock, mock_home: MagicMock, tmp_path
) -> None:
    cfg = tmp_path / "home"
    cfg.mkdir()
    legacy = cfg / ".config.json"
    legacy.write_text("{}", encoding="utf-8")
    mock_home.return_value = str(cfg)
    mock_exists.side_effect = lambda p: str(p) == str(legacy)
    env_mod.get_global_claude_file.cache_clear()
    path = get_global_claude_file()
    assert path == str(legacy)


@patch("claude_code.utils.env.os.path.expanduser", return_value="/h")
@patch("claude_code.utils.env.os.path.exists", return_value=False)
def test_get_global_claude_file_default_claude_json(
    _mock_exists: MagicMock, _mock_expand: MagicMock, monkeypatch: pytest.MonkeyPatch
) -> None:
    monkeypatch.delenv("CLAUDE_CONFIG_DIR", raising=False)
    env_mod.get_global_claude_file.cache_clear()
    p = get_global_claude_file()
    assert p == "/h/.claude.json"


@patch("socket.create_connection")
def test_has_internet_access_true_on_connect(mock_conn: MagicMock) -> None:
    env_mod.has_internet_access.cache_clear()
    assert has_internet_access() is True
    mock_conn.assert_called_once()


@patch("socket.create_connection", side_effect=OSError("offline"))
def test_has_internet_access_false_on_socket_error(_mock: MagicMock) -> None:
    env_mod.has_internet_access.cache_clear()
    assert has_internet_access() is False


@patch("claude_code.utils.env.os.path.exists", return_value=True)
def test_is_wsl_environment_true(_mock: MagicMock) -> None:
    env_mod.is_wsl_environment.cache_clear()
    assert is_wsl_environment() is True


@patch("claude_code.utils.env.os.path.exists", side_effect=RuntimeError("x"))
def test_is_wsl_environment_false_on_exception(_mock: MagicMock) -> None:
    env_mod.is_wsl_environment.cache_clear()
    assert is_wsl_environment() is False


def test_is_conductor_true_when_bundle_matches(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("__CFBundleIdentifier", "com.conductor.app")
    assert is_conductor() is True


@pytest.mark.parametrize(
    ("env", "expected"),
    [
        ({"CURSOR_TRACE_ID": "1"}, "cursor"),
        ({"VSCODE_GIT_ASKPASS_MAIN": "/x/cursor/y"}, "cursor"),
        ({"VSCODE_GIT_ASKPASS_MAIN": "/Windsurf/x"}, "windsurf"),
        ({"VSCODE_GIT_ASKPASS_MAIN": "/Antigravity/z"}, "antigravity"),
        ({"__CFBundleIdentifier": "com.vscodium.app"}, "codium"),
        ({"TERM_PROGRAM": "iTerm.app"}, "iterm"),
        ({"TERM_PROGRAM": "Apple_Terminal"}, "terminal"),
        ({"TERM_PROGRAM": "tmux"}, "tmux"),
        ({"KITTY_WINDOW_ID": "1"}, "kitty"),
        ({"ALACRITTY_SOCKET": "sock"}, "alacritty"),
        ({"WEZTERM_PANE": "p"}, "wezterm"),
    ],
)
def test_detect_terminal_branch_coverage(
    env: dict[str, str], expected: str, monkeypatch: pytest.MonkeyPatch
) -> None:
    for k in (
        "CURSOR_TRACE_ID",
        "VSCODE_GIT_ASKPASS_MAIN",
        "__CFBundleIdentifier",
        "TERM_PROGRAM",
        "KITTY_WINDOW_ID",
        "ALACRITTY_SOCKET",
        "WEZTERM_PANE",
    ):
        monkeypatch.delenv(k, raising=False)
    for k, v in env.items():
        monkeypatch.setenv(k, v)
    assert detect_terminal() == expected


def test_detect_editor_from_env_prefers_visual(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("VISUAL", "vim")
    monkeypatch.setenv("EDITOR", "nano")
    assert detect_editor_from_env() == "vim"


def test_detect_editor_from_env_falls_back_to_editor(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.delenv("VISUAL", raising=False)
    monkeypatch.setenv("EDITOR", "emacs")
    assert detect_editor_from_env() == "emacs"


@pytest.mark.parametrize("system, expected", [("Darwin", "darwin"), ("Windows", "win32"), ("Linux", "linux")])
def test_get_platform_maps_system(system: str, expected: str) -> None:
    with patch("platform.system", return_value=system):
        env_mod.get_platform.cache_clear()
        assert get_platform() == expected


def test_platform_helpers_consistent() -> None:
    with patch("platform.system", return_value="Darwin"):
        env_mod.get_platform.cache_clear()
        assert is_darwin() is True
        assert is_windows() is False
        assert is_linux() is False


def test_get_shell_defaults_to_bin_sh(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.delenv("SHELL", raising=False)
    assert get_shell() == "/bin/sh"


@patch("sys.stdout")
@patch("sys.stdin")
def test_is_interactive_shell_both_tty(mock_in: MagicMock, mock_out: MagicMock) -> None:
    mock_in.isatty.return_value = True
    mock_out.isatty.return_value = True
    assert is_interactive_shell() is True


@patch("socket.gethostname", return_value="box.local")
def test_get_hostname_uses_socket(mock_gh: MagicMock) -> None:
    env_mod.get_hostname.cache_clear()
    assert get_hostname() == "box.local"
    mock_gh.assert_called_once()


@patch("claude_code.utils.env.os.path.exists", return_value=True)
def test_is_docker_true_for_dockerenv(_mock: MagicMock) -> None:
    assert is_docker() is True


@patch("claude_code.utils.env.shutil.get_terminal_size", side_effect=OSError("no tty"))
def test_get_terminal_columns_fallback_80(_mock: MagicMock) -> None:
    assert get_terminal_columns() == 80


@patch("claude_code.utils.env.shutil.get_terminal_size", side_effect=OSError("no tty"))
def test_get_terminal_rows_fallback_24(_mock: MagicMock) -> None:
    assert get_terminal_rows() == 24


def test_find_dotenv_file_returns_none_when_missing(tmp_path, monkeypatch: pytest.MonkeyPatch) -> None:
    with patch("claude_code.utils.cwd.get_cwd", return_value=str(tmp_path)):
        assert find_dotenv_file(str(tmp_path), ".missing") is None


def test_find_dotenv_file_finds_closest(tmp_path, monkeypatch: pytest.MonkeyPatch) -> None:
    sub = tmp_path / "a" / "b"
    sub.mkdir(parents=True)
    env_file = tmp_path / "a" / ".env"
    env_file.write_text("X=1\n", encoding="utf-8")
    with patch("claude_code.utils.cwd.get_cwd", return_value=str(sub)):
        found = find_dotenv_file(str(sub), ".env")
    assert found == str(env_file.resolve())


def test_load_dotenv_file_false_when_missing(tmp_path) -> None:
    assert load_dotenv_file(tmp_path / "nope") is False


def test_load_dotenv_file_true_invokes_dotenv(tmp_path, monkeypatch: pytest.MonkeyPatch) -> None:
    p = tmp_path / ".env"
    p.write_text("Z=9\n", encoding="utf-8")
    monkeypatch.delenv("Z", raising=False)
    with patch("claude_code.utils.env.load_dotenv") as ld:
        ok = load_dotenv_file(p)
    assert ok is True
    ld.assert_called_once()


@patch("claude_code.utils.env.shutil.which", side_effect=lambda c: f"/bin/{c}")
def test_detect_package_managers_lists_available(_mock: MagicMock) -> None:
    env_mod.detect_package_managers.cache_clear()
    pms = detect_package_managers()
    assert "npm" in pms and "yarn" in pms and "pnpm" in pms


@patch("claude_code.utils.env.shutil.which", return_value=None)
def test_detect_runtimes_empty_when_missing(_mock: MagicMock) -> None:
    env_mod.detect_runtimes.cache_clear()
    assert detect_runtimes() == []
