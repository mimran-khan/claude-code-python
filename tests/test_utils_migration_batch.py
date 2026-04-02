"""Tests for newly migrated small utils modules."""

from __future__ import annotations

import pytest

from claude_code.utils.bundled_mode import is_in_bundled_mode, is_running_with_bun
from claude_code.utils.crypto_shim import random_uuid
from claude_code.utils.find_executable import find_executable
from claude_code.utils.json_read import strip_bom
from claude_code.utils.keyboard_shortcuts import MACOS_OPTION_SPECIAL_CHARS, is_macos_option_char
from claude_code.utils.message_predicates import is_human_turn
from claude_code.utils.object_group_by import object_group_by
from claude_code.utils.peer_address import parse_address
from claude_code.utils.system_prompt_type import SystemPrompt, as_system_prompt
from claude_code.utils.with_resolvers import with_resolvers
from claude_code.utils.worktree_mode_enabled import is_worktree_mode_enabled


def test_strip_bom() -> None:
    assert strip_bom("\ufeff{}") == "{}"
    assert strip_bom("{}") == "{}"


def test_object_group_by() -> None:
    got = object_group_by(["a", "bb", "c"], lambda s, i: len(s))
    assert got[1] == ["a", "c"]
    assert got[2] == ["bb"]


def test_worktree_mode_enabled() -> None:
    assert is_worktree_mode_enabled() is True


def test_random_uuid_format() -> None:
    u = random_uuid()
    assert len(u) == 36
    assert u.count("-") == 4


def test_with_resolvers() -> None:
    fut, resolve, _reject = with_resolvers()
    resolve("ok")
    assert fut.result(timeout=2) == "ok"


def test_parse_address() -> None:
    assert parse_address("uds:/tmp/x") == {"scheme": "uds", "target": "/tmp/x"}
    assert parse_address("bridge:abc") == {"scheme": "bridge", "target": "abc"}
    assert parse_address("/var/s") == {"scheme": "uds", "target": "/var/s"}
    assert parse_address("other") == {"scheme": "other", "target": "other"}


def test_find_executable() -> None:
    out = find_executable("python", ["-c", "1"])
    assert out["args"] == ["-c", "1"]
    assert isinstance(out["cmd"], str)


def test_system_prompt_brand() -> None:
    sp: SystemPrompt = as_system_prompt(["a", "b"])
    assert tuple(sp) == ("a", "b")


def test_macos_option_chars() -> None:
    assert "†" in MACOS_OPTION_SPECIAL_CHARS
    assert is_macos_option_char("†") is True
    assert is_macos_option_char("x") is False


def test_bundled_mode_defaults() -> None:
    assert is_running_with_bun() is False
    assert is_in_bundled_mode() is False


def test_is_human_turn() -> None:
    class U:
        type = "user"
        is_meta = False
        tool_use_result = None

    assert is_human_turn(U()) is True


def test_is_human_turn_meta() -> None:
    class U:
        type = "user"
        is_meta = True
        tool_use_result = None

    assert is_human_turn(U()) is False


@pytest.mark.asyncio
async def test_auth_portable_skips_non_darwin() -> None:
    from claude_code.utils import auth_portable

    if __import__("sys").platform == "darwin":
        pytest.skip("darwin-specific")
    await auth_portable.maybe_remove_api_key_from_mac_os_keychain_throws()
