"""Subprocess integration tests for the ``claude`` Typer CLI."""

from __future__ import annotations

import os

import pytest

from tests.integration.conftest import run_claude_cli


@pytest.mark.integration
def test_cli_help_exits_zero() -> None:
    proc = run_claude_cli(["--help"])
    assert proc.returncode == 0
    assert "Claude Code" in proc.stdout or "claude" in proc.stdout.lower()


@pytest.mark.integration
def test_cli_help_lists_version_option() -> None:
    proc = run_claude_cli(["--help"])
    assert proc.returncode == 0
    assert "--version" in proc.stdout or "-V" in proc.stdout


@pytest.mark.integration
def test_cli_help_lists_print_option() -> None:
    proc = run_claude_cli(["--help"])
    assert "--print" in proc.stdout


@pytest.mark.integration
def test_cli_help_lists_prompt_option() -> None:
    proc = run_claude_cli(["--help"])
    assert "--prompt" in proc.stdout or "-p" in proc.stdout


@pytest.mark.integration
def test_cli_version_short_flag() -> None:
    proc = run_claude_cli(["-V"])
    assert proc.returncode == 0
    assert "claude-code" in proc.stdout.lower() or "Session ID" in proc.stdout


@pytest.mark.integration
def test_cli_version_long_flag() -> None:
    proc = run_claude_cli(["--version"])
    assert proc.returncode == 0
    assert "Session ID" in proc.stdout or "claude" in proc.stdout.lower()


@pytest.mark.integration
def test_cli_version_subcommand() -> None:
    proc = run_claude_cli(["version"])
    assert proc.returncode == 0
    assert "Session ID" in proc.stdout


@pytest.mark.integration
def test_cli_doctor_runs() -> None:
    proc = run_claude_cli(["doctor"])
    assert proc.returncode == 0
    assert "doctor" in proc.stdout.lower()
    assert "Python" in proc.stdout
    assert "QueryEngine" in proc.stdout


@pytest.mark.integration
def test_cli_doctor_reports_git_resolution() -> None:
    proc = run_claude_cli(["doctor"])
    assert proc.returncode == 0
    assert "git:" in proc.stdout


@pytest.mark.integration
def test_cli_doctor_shows_config_path() -> None:
    proc = run_claude_cli(["doctor"])
    assert proc.returncode == 0
    assert "Global config" in proc.stdout


@pytest.mark.integration
def test_cli_doctor_with_api_key_shows_green_or_ok() -> None:
    proc = run_claude_cli(
        ["doctor"],
        env={**os.environ, "ANTHROPIC_API_KEY": "sk-test-integration"},
    )
    assert proc.returncode == 0
    assert "ANTHROPIC_API_KEY set: True" in proc.stdout


@pytest.mark.integration
def test_cli_config_shows_summary() -> None:
    proc = run_claude_cli(["config"])
    assert proc.returncode == 0
    assert "Config file:" in proc.stdout
    assert "Theme:" in proc.stdout
    assert "Release channel:" in proc.stdout


@pytest.mark.integration
def test_cli_config_shows_install_method() -> None:
    proc = run_claude_cli(["config"])
    assert proc.returncode == 0
    assert "Install method:" in proc.stdout


@pytest.mark.integration
def test_cli_config_edit_without_editor_exits_nonzero() -> None:
    proc = run_claude_cli(
        ["config", "--edit"],
        env={**{k: v for k, v in os.environ.items() if k not in ("EDITOR", "VISUAL")}},
    )
    assert proc.returncode == 1
    assert "EDITOR" in proc.stderr or "EDITOR" in proc.stdout


@pytest.mark.integration
def test_cli_chat_help() -> None:
    proc = run_claude_cli(["chat", "--help"])
    assert proc.returncode == 0
    assert "chat" in proc.stdout.lower()


@pytest.mark.integration
def test_cli_verbose_flag_on_help() -> None:
    proc = run_claude_cli(["--help"])
    assert "--verbose" in proc.stdout


@pytest.mark.integration
def test_cli_model_option_on_help() -> None:
    proc = run_claude_cli(["--help"])
    assert "--model" in proc.stdout or "-m" in proc.stdout


@pytest.mark.integration
def test_cli_print_without_prompt_exits_error() -> None:
    proc = run_claude_cli(["--print"])
    assert proc.returncode == 1
    assert "prompt" in proc.stdout.lower() or "prompt" in proc.stderr.lower()
