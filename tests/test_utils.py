"""Tests for path, git filesystem, file, env, and subprocess env utilities."""

from __future__ import annotations

import os
from pathlib import Path

import pytest

from claude_code.utils import env_utils
from claude_code.utils.file import path_exists, write_text_content
from claude_code.utils.git_filesystem import (
    clear_resolve_git_dir_cache,
    is_safe_ref_name,
    is_valid_git_sha,
)
from claude_code.utils.path_utils import expand_path
from claude_code.utils.subprocess_env import subprocess_env


def test_expand_path_rejects_null_byte() -> None:
    with pytest.raises(ValueError, match="null"):
        expand_path("foo\0bar")


def test_expand_path_empty_returns_base(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.chdir(tmp_path)
    out = expand_path("   ")
    assert os.path.isabs(out)


def test_is_safe_ref_name() -> None:
    assert is_safe_ref_name("main") is True
    assert is_safe_ref_name("feature/foo") is True
    assert is_safe_ref_name("") is False
    assert is_safe_ref_name("-bad") is False
    assert is_safe_ref_name("a..b") is False
    assert is_safe_ref_name("x/./y") is False


def test_is_valid_git_sha() -> None:
    sha40 = "a" * 40
    assert is_valid_git_sha(sha40) is True
    sha64 = "b" * 64
    assert is_valid_git_sha(sha64) is True
    assert is_valid_git_sha("gggg") is False
    assert is_valid_git_sha("a" * 39) is False


def test_clear_resolve_git_dir_cache_idempotent() -> None:
    clear_resolve_git_dir_cache()
    clear_resolve_git_dir_cache()


def test_path_exists_and_write_text_content(tmp_path: Path) -> None:
    fp = tmp_path / "t.txt"
    assert path_exists(str(fp)) is False
    write_text_content(str(fp), "hello\n", line_endings="LF")
    assert path_exists(str(fp)) is True
    assert fp.read_text(encoding="utf-8") == "hello\n"


def test_write_text_content_crlf(tmp_path: Path) -> None:
    fp = tmp_path / "crlf.txt"
    write_text_content(str(fp), "a\nb", line_endings="CRLF")
    raw = fp.read_bytes()
    assert b"\r\n" in raw


@pytest.mark.parametrize(
    "raw,expected",
    [
        ("1", True),
        ("TRUE", True),
        ("yes", True),
        ("on", True),
        ("0", False),
        ("false", False),
        ("", False),
    ],
)
def test_is_env_truthy(raw: str, expected: bool) -> None:
    assert env_utils.is_env_truthy(raw) is expected


def test_is_env_truthy_bool() -> None:
    assert env_utils.is_env_truthy(True) is True
    assert env_utils.is_env_truthy(False) is False


def test_parse_env_vars_valid() -> None:
    assert env_utils.parse_env_vars(["A=1", "B=two"]) == {"A": "1", "B": "two"}


def test_parse_env_vars_empty() -> None:
    assert env_utils.parse_env_vars(None) == {}
    assert env_utils.parse_env_vars([]) == {}


def test_parse_env_vars_invalid() -> None:
    with pytest.raises(ValueError, match="Invalid environment"):
        env_utils.parse_env_vars(["NO_EQUALS"])


def test_get_claude_config_home_dir_respects_env(monkeypatch: pytest.MonkeyPatch, tmp_path: Path) -> None:
    env_utils.get_claude_config_home_dir.cache_clear()
    custom = str(tmp_path / "cfg")
    monkeypatch.setenv("CLAUDE_CONFIG_DIR", custom)
    try:
        assert env_utils.get_claude_config_home_dir() == os.path.normpath(custom)
    finally:
        monkeypatch.delenv("CLAUDE_CONFIG_DIR", raising=False)
        env_utils.get_claude_config_home_dir.cache_clear()


def test_subprocess_env_scrub_when_flag_set(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("CLAUDE_CODE_SUBPROCESS_ENV_SCRUB", "1")
    base = {
        "PATH": "/usr/bin",
        "ANTHROPIC_API_KEY": "secret",
        "INPUT_ANTHROPIC_API_KEY": "also-secret",
    }
    out = subprocess_env(base)
    assert out["PATH"] == "/usr/bin"
    assert "ANTHROPIC_API_KEY" not in out
    assert "INPUT_ANTHROPIC_API_KEY" not in out


def test_subprocess_env_no_scrub_by_default(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.delenv("CLAUDE_CODE_SUBPROCESS_ENV_SCRUB", raising=False)
    base = {"ANTHROPIC_API_KEY": "x", "Y": "z"}
    out = subprocess_env(base)
    assert out["ANTHROPIC_API_KEY"] == "x"
