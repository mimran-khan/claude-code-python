"""Tests for plugin argument parsing (migrated from parseArgs.ts)."""

from __future__ import annotations

import pytest

from claude_code.commands.plugins.parse_args import (
    ParsedInstall,
    ParsedMarketplace,
    ParsedMenu,
    parse_plugin_args,
)


def test_empty_args_returns_menu() -> None:
    assert isinstance(parse_plugin_args(None), ParsedMenu)
    assert isinstance(parse_plugin_args(""), ParsedMenu)
    assert isinstance(parse_plugin_args("   "), ParsedMenu)


def test_install_plugin_at_marketplace() -> None:
    r = parse_plugin_args("install foo@bar")
    assert isinstance(r, ParsedInstall)
    assert r.plugin == "foo"
    assert r.marketplace == "bar"


def test_install_marketplace_url() -> None:
    r = parse_plugin_args("install https://example.com/m")
    assert isinstance(r, ParsedInstall)
    assert r.marketplace == "https://example.com/m"
    assert r.plugin is None


def test_marketplace_add() -> None:
    r = parse_plugin_args("marketplace add my-source")
    assert isinstance(r, ParsedMarketplace)
    assert r.action == "add"
    assert r.target == "my-source"


@pytest.mark.asyncio
async def test_install_slack_app_without_browser() -> None:
    from claude_code.commands.install_slack_app.install_slack_app import call

    r = await call()
    assert r.type == "text"
    assert "Slack" in r.value
