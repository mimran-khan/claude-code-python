"""Unit tests for pure helpers in ``claude_code.utils.permissions``."""

from __future__ import annotations

from unittest.mock import patch

import pytest

from claude_code.utils.permissions.bash_classifier import (
    classify_bash_command,
    is_classifier_permissions_enabled,
)
from claude_code.utils.permissions.dangerous_patterns import (
    is_dangerous_bash_permission,
    is_dangerous_powershell_permission,
)
from claude_code.utils.permissions.denial_tracking import (
    DENIAL_LIMITS,
    create_denial_tracking_state,
    get_denial_stats,
    record_denial,
    record_success,
    reset_denial_tracking,
    should_fallback_to_prompting,
)
from claude_code.utils.permissions.filesystem import (
    get_file_read_ignore_patterns,
    is_claude_settings_path,
    is_dangerous_directory,
    is_dangerous_file,
    matching_rule_for_input,
    normalize_case_for_comparison,
    path_in_allowed_working_path,
    path_in_working_path,
    relative_path,
    to_posix_path,
)
from claude_code.utils.permissions.path_validation import (
    expand_tilde,
    format_directory_list,
    get_glob_base_directory,
)
from claude_code.utils.permissions.rule_parser import (
    escape_rule_content,
    get_legacy_tool_names,
    normalize_legacy_tool_name,
    unescape_rule_content,
)


def test_normalize_case_lowers() -> None:
    assert normalize_case_for_comparison("/Foo/BAR") == "/foo/bar"


@pytest.mark.parametrize(
    "path, expected",
    [
        ("/proj/.claude/settings.json", True),
        ("/x/.claude.json", True),
        ("/repo/settings.json", True),
        ("/tmp/other.txt", False),
    ],
)
def test_is_claude_settings_path(path: str, expected: bool) -> None:
    assert is_claude_settings_path(path) is expected


@pytest.mark.parametrize(
    "basename",
    [".gitconfig", ".bashrc", ".mcp.json"],
)
def test_is_dangerous_file_detects(basename: str) -> None:
    assert is_dangerous_file(f"/home/u/{basename}") is True


def test_is_dangerous_file_case_insensitive() -> None:
    assert is_dangerous_file("/x/.GITCONFIG") is True


@pytest.mark.parametrize(
    "p",
    ["/repo/.git/config", r"C:\repo\.git", "/a/.vscode/settings.json"],
)
def test_is_dangerous_directory_paths(p: str) -> None:
    assert is_dangerous_directory(p) is True


def test_relative_path_posix_style(tmp_path) -> None:
    a = tmp_path / "a"
    b = tmp_path / "a" / "b" / "c.txt"
    a.mkdir()
    b.parent.mkdir(parents=True)
    b.write_text("x", encoding="utf-8")
    rel = relative_path(str(a), str(b))
    assert "/" in rel
    assert "\\" not in rel


def test_to_posix_path() -> None:
    assert to_posix_path(r"a\b\c") == "a/b/c"


def test_path_in_working_path_true(tmp_path) -> None:
    sub = tmp_path / "s"
    sub.mkdir()
    f = sub / "f.txt"
    f.write_text("z", encoding="utf-8")
    assert path_in_working_path(str(f), str(tmp_path)) is True


def test_path_in_allowed_working_path_extra(tmp_path) -> None:
    other = tmp_path / "other"
    other.mkdir()
    f = other / "x"
    f.write_text("1", encoding="utf-8")
    assert path_in_allowed_working_path(str(f), str(tmp_path), [str(other)]) is True


def test_matching_rule_for_input_tool_mismatch() -> None:
    assert matching_rule_for_input("Bash", {"command": "ls"}, ["Read(*)"], "/tmp") is None


def test_matching_rule_for_input_tool_wide_rule() -> None:
    r = matching_rule_for_input("Read", {}, ["Read"], "/tmp")
    assert r == "Read"


def test_get_file_read_ignore_patterns_non_empty() -> None:
    pats = get_file_read_ignore_patterns()
    assert "*.pyc" in pats


def test_format_directory_list_short() -> None:
    assert "'a'" in format_directory_list(["a", "b"])


def test_format_directory_list_truncates() -> None:
    dirs = [f"d{i}" for i in range(10)]
    s = format_directory_list(dirs)
    assert "more" in s


@pytest.mark.parametrize(
    "pattern, expected_end",
    [
        ("/a/b/*.txt", "/a/b"),
        ("/no/glob/here", "/no/glob/here"),
    ],
)
def test_get_glob_base_directory_unix(pattern: str, expected_end: str) -> None:
    with patch("claude_code.utils.permissions.path_validation.get_platform", return_value="linux"):
        base = get_glob_base_directory(pattern)
    assert base == expected_end


def test_get_glob_base_directory_windows_backslash() -> None:
    with patch("claude_code.utils.permissions.path_validation.get_platform", return_value="windows"):
        base = get_glob_base_directory(r"C:\x\*.log")
    assert "x" in base


def test_expand_tilde_slash(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("HOME", "/home/testuser")
    with patch("os.path.expanduser", return_value="/home/testuser"):
        assert expand_tilde("~/doc").startswith("/home/testuser")


def test_expand_tilde_unknown_prefix_unchanged() -> None:
    assert expand_tilde("/abs/path") == "/abs/path"


def test_denial_tracking_flow() -> None:
    s = create_denial_tracking_state()
    assert s.consecutive_denials == 0
    s2 = record_denial(s)
    assert s2.consecutive_denials == 1
    s3 = record_success(s2)
    assert s3.consecutive_denials == 0
    assert s3.total_denials == 1


def test_record_success_noop_when_zero() -> None:
    s = create_denial_tracking_state()
    assert record_success(s) is s


def test_should_fallback_consecutive_limit() -> None:
    s = create_denial_tracking_state()
    for _ in range(DENIAL_LIMITS.max_consecutive):
        s = record_denial(s)
    assert should_fallback_to_prompting(s) is True


def test_should_fallback_total_limit() -> None:
    s = create_denial_tracking_state()
    for _ in range(DENIAL_LIMITS.max_total - 1):
        s = record_denial(s)
        s = record_success(s)
    s = record_denial(s)
    assert should_fallback_to_prompting(s) is True


def test_get_denial_stats_keys() -> None:
    stats = get_denial_stats(create_denial_tracking_state())
    assert set(stats.keys()) >= {"consecutive_denials", "total_denials", "should_prompt"}


def test_reset_denial_tracking_fresh() -> None:
    s = reset_denial_tracking()
    assert s.total_denials == 0


@pytest.mark.parametrize(
    "content, dangerous",
    [
        (None, False),
        ("", False),
        ("python", True),
        ("python3:*", True),
        ("ls", False),
    ],
)
def test_is_dangerous_bash_permission(content: str | None, dangerous: bool) -> None:
    assert is_dangerous_bash_permission(content) is dangerous


def test_is_dangerous_bash_includes_extra_when_user_type_ant(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("USER_TYPE", "ant")
    assert is_dangerous_bash_permission("curl") is True


@pytest.mark.parametrize(
    "content, dangerous",
    [
        ("pwsh", True),
        ("Invoke-Expression", True),
        ("Get-ChildItem", False),
    ],
)
def test_is_dangerous_powershell_permission(content: str, dangerous: bool) -> None:
    assert is_dangerous_powershell_permission(content) is dangerous


def test_escape_unescape_roundtrip() -> None:
    raw = r'echo \(parens\) \\'
    esc = escape_rule_content(raw)
    assert unescape_rule_content(esc) == raw


def test_normalize_legacy_tool_name_maps_task() -> None:
    assert normalize_legacy_tool_name("Task") == "Agent"


def test_get_legacy_tool_names_for_agent() -> None:
    assert "Task" in get_legacy_tool_names("Agent")


def test_is_classifier_permissions_disabled() -> None:
    assert is_classifier_permissions_enabled() is False


@pytest.mark.asyncio
async def test_classify_bash_command_stub_returns_no_match() -> None:
    r = await classify_bash_command("echo hi", "/tmp", [], "allow")
    assert r.matches is False
    assert r.confidence == "high"
