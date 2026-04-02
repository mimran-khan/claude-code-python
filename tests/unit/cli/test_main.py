"""Unit tests for ``claude_code.cli.main`` (Typer entry, helpers, slash commands)."""

from __future__ import annotations

from unittest.mock import MagicMock, patch

import pytest
from typer.testing import CliRunner

from claude_code.cli import main as cli_main
from claude_code.engine.query_engine import QueryEngineConfig, SDKResultMessage


@pytest.fixture
def runner() -> CliRunner:
    return CliRunner()


def test_cli_version_exits_zero(runner: CliRunner) -> None:
    result = runner.invoke(cli_main.app, ["--version"])
    assert result.exit_code == 0
    assert "claude-code" in result.stdout
    assert "Session ID" in result.stdout


def test_cli_help_exits_zero(runner: CliRunner) -> None:
    result = runner.invoke(cli_main.app, ["--help"])
    assert result.exit_code == 0
    assert "Claude Code" in result.stdout


def test_package_version_fallback_when_metadata_missing() -> None:
    with patch.object(cli_main.metadata, "version", side_effect=cli_main.metadata.PackageNotFoundError):
        assert cli_main._package_version() == "0.1.0"


def test_print_mode_without_prompt_exits_one(runner: CliRunner) -> None:
    result = runner.invoke(cli_main.app, ["--print"])
    assert result.exit_code == 1
    assert "no prompt" in result.stdout.lower() or "no prompt" in (result.stderr or "").lower()


def test_chat_print_without_prompt_exits_one(runner: CliRunner) -> None:
    result = runner.invoke(cli_main.app, ["chat", "--print"])
    assert result.exit_code == 1


class _StubQueryEngine:
    """Minimal stand-in for CLI print-mode tests (no API)."""

    def __init__(self, config: QueryEngineConfig) -> None:
        self._config = config

    def get_messages(self) -> list:
        return []

    async def submit_message(self, user_text: str, options=None):
        yield SDKResultMessage(
            type="result",
            subtype="success",
            session_id="",
            uuid="stub",
            is_error=False,
            result="stub-result",
        )


def test_print_mode_with_prompt_runs_stub_engine(runner: CliRunner) -> None:
    with patch.object(cli_main, "QueryEngine", _StubQueryEngine):
        result = runner.invoke(cli_main.app, ["--print", "--prompt", "hello"])
    assert result.exit_code == 0
    assert "stub-result" in result.stdout


def test_config_cmd_shows_summary(runner: CliRunner) -> None:
    fake_cfg = MagicMock()
    fake_cfg.theme = "dark"
    fake_cfg.release_channel = "stable"
    fake_cfg.verbose_mode = False
    fake_cfg.install_method = "pip"
    with (
        patch.object(cli_main, "get_config_path", return_value="/tmp/claude-config.json"),
        patch.object(cli_main, "get_global_config", return_value=fake_cfg),
        patch.object(cli_main.os.path, "isfile", return_value=False),
    ):
        result = runner.invoke(cli_main.app, ["config"])
    assert result.exit_code == 0
    assert "Config file:" in result.stdout
    assert "Theme: dark" in result.stdout


@pytest.mark.asyncio
async def test_handle_slash_exit_breaks_loop() -> None:
    engine = MagicMock()
    engine.get_messages.return_value = []
    new_engine, stop = cli_main._handle_slash_command(
        "exit",
        engine=engine,
        model=None,
        verbose=False,
    )
    assert stop is True
    assert new_engine is engine


@pytest.mark.asyncio
async def test_handle_slash_clear_returns_new_engine() -> None:
    engine = MagicMock()
    with patch.object(cli_main, "_create_cli_query_engine") as mock_create:
        mock_create.return_value = MagicMock(name="fresh")
        new_engine, stop = cli_main._handle_slash_command(
            "clear",
            engine=engine,
            model="m",
            verbose=True,
        )
    assert stop is False
    assert new_engine is mock_create.return_value
    mock_create.assert_called_once_with(model="m", verbose=True)
