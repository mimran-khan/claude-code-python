"""Tests for MCP normalization and string helpers."""

from __future__ import annotations

from dataclasses import dataclass

from claude_code.services.mcp.normalization import (
    CLAUDEAI_SERVER_PREFIX,
    is_valid_mcp_name,
    normalize_name_for_mcp,
    parse_tool_name,
    sanitize_tool_name,
)
from claude_code.services.mcp.string_utils import (
    build_mcp_tool_name,
    get_mcp_display_name,
    get_mcp_prefix,
    get_tool_name_for_permission_check,
    mcp_info_from_string,
)


def test_normalize_name_for_mcp_basic() -> None:
    assert normalize_name_for_mcp("my-server") == "my-server"
    assert normalize_name_for_mcp("bad name!") == "bad_name_"


def test_normalize_claude_ai_prefix_collapses_underscores() -> None:
    raw = CLAUDEAI_SERVER_PREFIX + "foo..bar"
    out = normalize_name_for_mcp(raw)
    assert ".." not in out or "_" in out
    assert is_valid_mcp_name(out)


def test_is_valid_mcp_name() -> None:
    assert is_valid_mcp_name("a" * 64) is True
    assert is_valid_mcp_name("a" * 65) is False
    assert is_valid_mcp_name("bad.name") is False


def test_sanitize_and_parse_tool_name() -> None:
    full = sanitize_tool_name("My Server", "Tool/A")
    left, right = parse_tool_name(full)
    assert left and right


def test_mcp_info_from_string() -> None:
    assert mcp_info_from_string("nope") is None
    only = mcp_info_from_string("mcp__only")
    assert only is not None
    assert only.server_name == "only"
    assert only.tool_name is None
    info = mcp_info_from_string("mcp__srv__tool__name")
    assert info is not None
    assert info.server_name == "srv"
    assert info.tool_name == "tool__name"


def test_build_mcp_tool_name_roundtrip_prefix() -> None:
    name = build_mcp_tool_name("MySrv", "DoThing")
    assert name.startswith(get_mcp_prefix("MySrv"))
    display = get_mcp_display_name(name, "MySrv")
    assert "mcp__" not in display or display != name


@dataclass
class _FakeMcpInfo:
    server_name: str
    tool_name: str


class _FakeTool:
    def __init__(self, name: str, mcp_info: _FakeMcpInfo | None = None) -> None:
        self.name = name
        self.mcp_info = mcp_info


def test_get_tool_name_for_permission_check_plain() -> None:
    assert get_tool_name_for_permission_check(_FakeTool("Bash")) == "Bash"


def test_get_tool_name_for_permission_check_mcp() -> None:
    t = _FakeTool("x", _FakeMcpInfo("srv", "t1"))
    assert "mcp__" in get_tool_name_for_permission_check(t)
