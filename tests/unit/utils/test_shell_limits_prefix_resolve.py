"""Unit tests for ``claude_code.utils.shell`` helpers."""

from __future__ import annotations

from unittest.mock import MagicMock, patch

import pytest

from claude_code.utils.bash.command_spec import CommandSpec
from claude_code.utils.shell.output_limits import (
    BASH_MAX_OUTPUT_DEFAULT,
    BASH_MAX_OUTPUT_UPPER_LIMIT,
    get_max_output_length,
)
from claude_code.utils.shell.read_only_validation import (
    ExternalCommandConfig,
    contains_vulnerable_unc_path,
    validate_flag_argument,
    validate_flags,
)
from claude_code.utils.shell.resolve_default_shell import resolve_default_shell
from claude_code.utils.shell.spec_prefix import DEPTH_RULES, build_prefix


@pytest.fixture(autouse=True)
def _clear_output_env(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.delenv("BASH_MAX_OUTPUT_LENGTH", raising=False)
    yield


@pytest.mark.parametrize(
    "value, arg_type, ok",
    [
        ("", "none", False),
        ("42", "number", True),
        ("x", "number", False),
        ("anything", "string", True),
        ("a", "char", True),
        ("ab", "char", False),
        ("{}", "{}", True),
        ("EOF", "EOF", True),
        ("x", "unknown", False),
    ],
)
def test_validate_flag_argument(value: str, arg_type: str, ok: bool) -> None:
    assert validate_flag_argument(value, arg_type) is ok


@pytest.mark.parametrize(
    "cmd, vulnerable",
    [
        (r"\\server@ssl\share", True),
        ("normal/path", False),
    ],
)
def test_contains_vulnerable_unc_path_respects_platform(
    cmd: str, vulnerable: bool, monkeypatch: pytest.MonkeyPatch
) -> None:
    with patch("claude_code.utils.shell.read_only_validation.get_platform", return_value="windows"):
        assert contains_vulnerable_unc_path(cmd) is vulnerable


def test_contains_vulnerable_unc_path_false_on_linux() -> None:
    with patch("claude_code.utils.shell.read_only_validation.get_platform", return_value="linux"):
        assert contains_vulnerable_unc_path(r"\\evil@ssl\a") is False


def test_validate_flags_simple_safe_flag() -> None:
    cfg = ExternalCommandConfig(safe_flags={"-v": "none"})
    assert validate_flags(["-v"], 0, cfg) is True


def test_validate_flags_unknown_flag_returns_false() -> None:
    cfg = ExternalCommandConfig(safe_flags={})
    assert validate_flags(["-z"], 0, cfg) is False


def test_get_max_output_length_default() -> None:
    assert get_max_output_length() == BASH_MAX_OUTPUT_DEFAULT


@pytest.mark.parametrize(
    "env_val, expected",
    [
        ("0", BASH_MAX_OUTPUT_DEFAULT),
        ("-5", BASH_MAX_OUTPUT_DEFAULT),
        ("notint", BASH_MAX_OUTPUT_DEFAULT),
        ("500", 500),
        ("9999999", BASH_MAX_OUTPUT_UPPER_LIMIT),
    ],
)
def test_get_max_output_length_parsing(
    env_val: str, expected: int, monkeypatch: pytest.MonkeyPatch
) -> None:
    monkeypatch.setenv("BASH_MAX_OUTPUT_LENGTH", env_val)
    assert get_max_output_length() == expected


def test_depth_rules_has_expected_keys() -> None:
    assert DEPTH_RULES["git push"] == 2
    assert DEPTH_RULES["kubectl"] == 3


@pytest.mark.asyncio
async def test_build_prefix_stops_at_python_c() -> None:
    p = await build_prefix("python3", ["-c", "print(1)"], None)
    assert p == "python3"


@pytest.mark.asyncio
async def test_build_prefix_includes_depth_for_docker() -> None:
    p = await build_prefix("docker", ["run", "img"], None)
    assert p.startswith("docker")


def test_resolve_default_shell_bash_when_unset() -> None:
    with patch(
        "claude_code.utils.shell.resolve_default_shell.get_merged_settings",
        return_value={},
    ):
        assert resolve_default_shell() == "bash"


def test_resolve_default_shell_from_settings() -> None:
    with patch(
        "claude_code.utils.shell.resolve_default_shell.get_merged_settings",
        return_value={"defaultShell": "powershell"},
    ):
        assert resolve_default_shell() == "powershell"


def test_resolve_default_shell_invalid_type_ignored() -> None:
    with patch(
        "claude_code.utils.shell.resolve_default_shell.get_merged_settings",
        return_value={"defaultShell": 123},
    ):
        assert resolve_default_shell() == "bash"


@pytest.mark.asyncio
async def test_build_prefix_with_simple_spec_subcommand() -> None:
    spec = CommandSpec(
        name="git",
        subcommands=[
            CommandSpec(name="status"),
        ],
    )
    p = await build_prefix("git", ["status"], spec)
    assert "git" in p and "status" in p


@pytest.mark.asyncio
async def test_build_prefix_empty_args_is_just_command() -> None:
    p = await build_prefix("ls", [], None)
    assert p == "ls"
