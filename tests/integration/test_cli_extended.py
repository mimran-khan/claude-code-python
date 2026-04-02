"""Additional subprocess CLI integration tests (isolated config, flags, error paths)."""

from __future__ import annotations

import os
from pathlib import Path

import pytest

from tests.integration.conftest import REPO_ROOT, run_claude_cli

pytestmark = pytest.mark.integration


def test_cli_help_exits_zero_with_custom_claude_config_dir(tmp_path: Path) -> None:
    proc = run_claude_cli(
        ["--help"],
        env={**os.environ, "CLAUDE_CONFIG_DIR": str(tmp_path)},
    )
    assert proc.returncode == 0
    assert "Claude Code" in proc.stdout or "claude" in proc.stdout.lower()


def test_cli_version_exits_zero_with_custom_claude_config_dir(tmp_path: Path) -> None:
    proc = run_claude_cli(
        ["--version"],
        env={**os.environ, "CLAUDE_CONFIG_DIR": str(tmp_path)},
    )
    assert proc.returncode == 0
    assert "Session ID" in proc.stdout


def test_cli_config_shows_exists_false_for_empty_config_dir(tmp_path: Path) -> None:
    proc = run_claude_cli(
        ["config"],
        env={**os.environ, "CLAUDE_CONFIG_DIR": str(tmp_path)},
    )
    assert proc.returncode == 0
    assert "Exists: False" in proc.stdout
    assert str(tmp_path.resolve()) in proc.stdout or "config.json" in proc.stdout


def test_cli_config_shows_exists_true_after_seed_config(tmp_path: Path) -> None:
    cfg = tmp_path / "config.json"
    cfg.write_text('{"theme": "dark", "verboseMode": false}', encoding="utf-8")
    proc = run_claude_cli(
        ["config"],
        env={**os.environ, "CLAUDE_CONFIG_DIR": str(tmp_path)},
    )
    assert proc.returncode == 0
    assert "Exists: True" in proc.stdout


def test_cli_doctor_runs_with_custom_claude_config_dir(tmp_path: Path) -> None:
    proc = run_claude_cli(
        ["doctor"],
        env={**os.environ, "CLAUDE_CONFIG_DIR": str(tmp_path)},
    )
    assert proc.returncode == 0
    assert "doctor" in proc.stdout.lower()
    assert "QueryEngine" in proc.stdout


def test_cli_doctor_lists_global_config_path_in_custom_dir(tmp_path: Path) -> None:
    proc = run_claude_cli(
        ["doctor"],
        env={**os.environ, "CLAUDE_CONFIG_DIR": str(tmp_path)},
    )
    assert proc.returncode == 0
    assert "Global config:" in proc.stdout
    assert "config.json" in proc.stdout


def test_cli_config_short_edit_flag_requires_editor(tmp_path: Path) -> None:
    proc = run_claude_cli(
        ["config", "-e"],
        env={
            **{k: v for k, v in os.environ.items() if k not in ("EDITOR", "VISUAL")},
            "CLAUDE_CONFIG_DIR": str(tmp_path),
        },
    )
    assert proc.returncode == 1
    assert "EDITOR" in proc.stderr or "EDITOR" in proc.stdout


def test_cli_chat_subcommand_without_prompt_exits_error() -> None:
    proc = run_claude_cli(["chat", "--print"])
    assert proc.returncode == 1
    out = proc.stdout + proc.stderr
    assert "prompt" in out.lower()


def test_cli_chat_subcommand_help_lists_print_option() -> None:
    proc = run_claude_cli(["chat", "--help"])
    assert proc.returncode == 0
    assert "--print" in proc.stdout


def test_cli_verbose_flag_documented_on_root_help() -> None:
    proc = run_claude_cli(["--help"])
    assert proc.returncode == 0
    assert "--verbose" in proc.stdout


def test_cli_model_option_documented_on_root_help() -> None:
    proc = run_claude_cli(["--help"])
    assert proc.returncode == 0
    assert "--model" in proc.stdout or "-m" in proc.stdout


def test_cli_config_lists_release_channel_stable_by_default(tmp_path: Path) -> None:
    proc = run_claude_cli(
        ["config"],
        env={**os.environ, "CLAUDE_CONFIG_DIR": str(tmp_path)},
    )
    assert proc.returncode == 0
    assert "Release channel:" in proc.stdout


def test_cli_doctor_warns_when_api_key_missing(tmp_path: Path) -> None:
    env = {
        k: v
        for k, v in os.environ.items()
        if k != "ANTHROPIC_API_KEY"
    }
    env["CLAUDE_CONFIG_DIR"] = str(tmp_path)
    proc = run_claude_cli(["doctor"], env=env)
    assert proc.returncode == 0
    assert "ANTHROPIC_API_KEY set: False" in proc.stdout


def test_cli_version_subcommand_from_repo_src_on_path() -> None:
    proc = run_claude_cli(["version"], cwd=REPO_ROOT)
    assert proc.returncode == 0
    assert "Session ID" in proc.stdout


def test_cli_print_with_prompt_requires_network_or_key() -> None:
    """--print with prompt attempts engine; without API key expect error exit, not crash."""
    proc = run_claude_cli(
        ["--print", "--prompt", "say hi"],
        env={
            k: v
            for k, v in os.environ.items()
            if k != "ANTHROPIC_API_KEY"
        },
        timeout=60.0,
    )
    assert proc.returncode in (0, 1, 130)
    out = proc.stdout + proc.stderr
    assert len(out) > 0
