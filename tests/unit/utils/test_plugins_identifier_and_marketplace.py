"""Unit tests for ``claude_code.utils.plugins.identifier`` and marketplace parsing."""

from __future__ import annotations

import stat
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from claude_code.utils.plugins.identifier import (
    PluginIdentifier,
    format_plugin_id,
    is_scoped_plugin_id,
    parse_plugin_identifier,
    scope_to_setting_source,
    setting_source_to_scope,
)
from claude_code.utils.plugins.marketplace_parser import (
    MarketplaceDirectorySource,
    MarketplaceFileSource,
    MarketplaceGitSource,
    MarketplaceGithubShorthand,
    MarketplaceParseError,
    MarketplaceUrlSource,
    parse_marketplace_input,
)


@pytest.mark.parametrize(
    "ident, name, marketplace, version",
    [
        ("foo", "foo", None, None),
        ("foo@mp", "foo", "mp", None),
        ("foo@mp:1.0", "foo", "mp", "1.0"),
        ("pkg:2@market:edge", "pkg:2", "market", "edge"),
    ],
)
def test_parse_plugin_identifier(
    ident: str, name: str, marketplace: str | None, version: str | None
) -> None:
    p = parse_plugin_identifier(ident)
    assert p.name == name
    assert p.marketplace == marketplace
    assert p.version == version


def test_plugin_identifier_full_id_with_marketplace() -> None:
    pid = PluginIdentifier("n", marketplace="m")
    assert pid.full_id == "n@m"


def test_plugin_identifier_full_id_name_only() -> None:
    assert PluginIdentifier("solo").full_id == "solo"


@pytest.mark.parametrize(
    "scope, source",
    [
        ("user", "userSettings"),
        ("project", "projectSettings"),
        ("local", "localSettings"),
        ("managed", "policySettings"),
        ("unknown", "userSettings"),
    ],
)
def test_scope_to_setting_source(scope: str, source: str) -> None:
    assert scope_to_setting_source(scope) == source


@pytest.mark.parametrize(
    "source, scope",
    [
        ("userSettings", "user"),
        ("projectSettings", "project"),
        ("localSettings", "local"),
        ("policySettings", "managed"),
    ],
)
def test_setting_source_to_scope(source: str, scope: str) -> None:
    assert setting_source_to_scope(source) == scope


def test_setting_source_to_scope_unknown_key_defaults_user() -> None:
    assert setting_source_to_scope("not_a_valid_key") == "user"  # type: ignore[arg-type]


def test_format_plugin_id() -> None:
    assert format_plugin_id("a", "b") == "a@b"
    assert format_plugin_id("a") == "a"


@pytest.mark.parametrize("pid, scoped", [("a@b", True), ("plain", False)])
def test_is_scoped_plugin_id(pid: str, scoped: bool) -> None:
    assert is_scoped_plugin_id(pid) is scoped


@pytest.mark.asyncio
async def test_parse_marketplace_input_ssh_git() -> None:
    r = await parse_marketplace_input("git@github.com:org/repo.git#v1")
    assert isinstance(r, MarketplaceGitSource)
    assert "git@github.com:org/repo.git" in r.url
    assert r.ref == "v1"


@pytest.mark.asyncio
async def test_parse_marketplace_input_https_git_suffix() -> None:
    r = await parse_marketplace_input("https://example.com/foo.git")
    assert isinstance(r, MarketplaceGitSource)
    assert r.url.endswith(".git")


@pytest.mark.asyncio
async def test_parse_marketplace_input_github_host_becomes_git() -> None:
    r = await parse_marketplace_input("https://github.com/org/repo")
    assert isinstance(r, MarketplaceGitSource)
    assert r.url.endswith(".git")


@pytest.mark.asyncio
async def test_parse_marketplace_input_plain_https_url() -> None:
    r = await parse_marketplace_input("https://cdn.example.com/file.zip")
    assert isinstance(r, MarketplaceUrlSource)


@pytest.mark.asyncio
async def test_parse_marketplace_input_github_shorthand() -> None:
    r = await parse_marketplace_input("org/repo#tag")
    assert isinstance(r, MarketplaceGithubShorthand)
    assert r.repo == "org/repo"
    assert r.ref == "tag"


@pytest.mark.asyncio
async def test_parse_marketplace_input_shorthand_with_colon_returns_none() -> None:
    r = await parse_marketplace_input("a:b/c")
    assert r is None


@pytest.mark.asyncio
async def test_parse_marketplace_local_json_file(tmp_path) -> None:
    p = tmp_path / "m.json"
    p.write_text("{}", encoding="utf-8")

    st = MagicMock()
    st.st_mode = stat.S_IFREG
    fs = MagicMock()
    fs.stat = AsyncMock(return_value=st)

    with patch("claude_code.utils.plugins.marketplace_parser.get_fs_implementation", return_value=fs):
        r = await parse_marketplace_input(str(p))
    assert isinstance(r, MarketplaceFileSource)
    assert r.path.endswith("m.json")


@pytest.mark.asyncio
async def test_parse_marketplace_local_directory(tmp_path) -> None:
    d = tmp_path / "dir"
    d.mkdir()

    st = MagicMock()
    st.st_mode = stat.S_IFDIR
    fs = MagicMock()
    fs.stat = AsyncMock(return_value=st)

    with patch("claude_code.utils.plugins.marketplace_parser.get_fs_implementation", return_value=fs):
        r = await parse_marketplace_input(str(d))
    assert isinstance(r, MarketplaceDirectorySource)


@pytest.mark.asyncio
async def test_parse_marketplace_missing_path_error(tmp_path) -> None:
    missing = tmp_path / "nope.json"
    fs = MagicMock()
    fs.stat = AsyncMock(side_effect=FileNotFoundError())

    with patch("claude_code.utils.plugins.marketplace_parser.get_fs_implementation", return_value=fs):
        r = await parse_marketplace_input(str(missing))
    assert isinstance(r, MarketplaceParseError)
    assert r.error.startswith("Cannot access path:")


@pytest.mark.asyncio
async def test_parse_marketplace_non_json_file_error(tmp_path) -> None:
    p = tmp_path / "x.txt"
    p.write_text("hi", encoding="utf-8")
    st = MagicMock()
    st.st_mode = stat.S_IFREG
    fs = MagicMock()
    fs.stat = AsyncMock(return_value=st)

    with patch("claude_code.utils.plugins.marketplace_parser.get_fs_implementation", return_value=fs):
        r = await parse_marketplace_input(str(p))
    assert isinstance(r, MarketplaceParseError)
    assert ".json" in r.error


@pytest.mark.asyncio
async def test_parse_marketplace_whitespace_only_returns_none() -> None:
    assert await parse_marketplace_input("   ") is None


@pytest.mark.asyncio
async def test_parse_marketplace_input_from_parse_marketplace_input_shim() -> None:
    from claude_code.utils.plugins.parse_marketplace_input import parse_marketplace_input as shim

    r = await shim("https://example.com/x.zip")
    assert isinstance(r, MarketplaceUrlSource)
