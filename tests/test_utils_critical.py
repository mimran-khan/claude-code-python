"""Tests for git, env, file, subprocess, and config_utils helpers."""

from __future__ import annotations

import json
import os
from pathlib import Path

import pytest

from claude_code.utils.config_utils import apply_defaults, load_json_config, merge_settings
from claude_code.utils.env import (
    find_dotenv_file,
    load_dotenv_file,
    merge_env_with_defaults,
)
from claude_code.utils.file import detect_file_encoding, is_probably_binary, read_file_safe
from claude_code.utils.git import (
    exec_git_command,
    get_branch,
    get_default_branch_async,
    get_is_git,
    git_exe,
)
from claude_code.utils.subprocess import run_async


def test_git_exe_resolves() -> None:
    g = git_exe()
    assert g
    assert os.path.isabs(g) or g == "git"


@pytest.mark.asyncio
async def test_get_is_git_tmp_not_repo() -> None:
    assert await get_is_git("/tmp") is False


@pytest.mark.asyncio
async def test_get_is_git_this_repo() -> None:
    here = Path(__file__).resolve().parent.parent
    assert await get_is_git(str(here)) is True


@pytest.mark.asyncio
async def test_get_branch_this_repo() -> None:
    here = Path(__file__).resolve().parent.parent
    b = await get_branch(str(here))
    assert isinstance(b, str)
    assert len(b) > 0


@pytest.mark.asyncio
async def test_get_default_branch_async() -> None:
    here = Path(__file__).resolve().parent.parent
    main = await get_default_branch_async(str(here))
    assert main in ("main", "master") or len(main) > 0


@pytest.mark.asyncio
async def test_exec_git_command() -> None:
    here = Path(__file__).resolve().parent.parent
    out = await exec_git_command(["rev-parse", "--is-inside-work-tree"], cwd=str(here))
    assert out.strip().lower() == "true"


def test_merge_env_with_defaults() -> None:
    assert merge_env_with_defaults({"A": "2"}, {"A": "1", "B": "x"}) == {
        "A": "2",
        "B": "x",
    }


def test_find_and_load_dotenv(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    d = tmp_path / "proj"
    d.mkdir()
    (d / ".env").write_text("DOTENV_TEST_XYZZY=fromfile\n", encoding="utf-8")
    monkeypatch.delenv("DOTENV_TEST_XYZZY", raising=False)
    assert find_dotenv_file(str(d), ".env") == str(d / ".env")
    assert load_dotenv_file(d / ".env") is True
    assert os.environ.get("DOTENV_TEST_XYZZY") == "fromfile"


def test_is_probably_binary_and_encoding_utf8(tmp_path: Path) -> None:
    p = tmp_path / "t.txt"
    p.write_text("hello\nworld\n", encoding="utf-8")
    assert is_probably_binary(str(p)) is False
    assert detect_file_encoding(str(p)) == "utf-8"


def test_read_file_safe_skips_binary(tmp_path: Path) -> None:
    p = tmp_path / "b.bin"
    p.write_bytes(b"\x00\x01\x02\x03")
    assert read_file_safe(str(p)) is None


@pytest.mark.asyncio
async def test_run_async_echo() -> None:
    if os.name == "nt":
        r = await run_async(
            ["cmd", "/c", "echo", "hi"],
            timeout=10.0,
        )
    else:
        r = await run_async(["/bin/sh", "-c", "echo hi"], timeout=10.0)
    assert r.returncode == 0
    assert "hi" in r.stdout


@pytest.mark.asyncio
async def test_run_async_timeout() -> None:
    if os.name == "nt":
        pytest.skip("sleep binary differs on Windows")
    r = await run_async(["/bin/sleep", "60"], timeout=0.1)
    assert r.returncode == -9
    assert "timed out" in r.stderr


def test_load_json_config_and_merge(tmp_path: Path) -> None:
    p = tmp_path / "c.json"
    p.write_text(json.dumps({"a": 1, "nested": {"x": 1}}), encoding="utf-8")
    data = load_json_config(str(p))
    assert data["a"] == 1
    merged = merge_settings(data, {"a": 2, "nested": {"y": 2}})
    assert merged["a"] == 2
    assert merged["nested"]["x"] == 1
    assert merged["nested"]["y"] == 2
    with_defaults = apply_defaults({"a": 10}, {"a": 0, "b": 3})
    assert with_defaults == {"a": 10, "b": 3}


def test_load_json_config_rejects_non_object(tmp_path: Path) -> None:
    p = tmp_path / "arr.json"
    p.write_text("[1,2]", encoding="utf-8")
    from claude_code.utils.errors import ConfigParseError

    with pytest.raises(ConfigParseError):
        load_json_config(str(p))
