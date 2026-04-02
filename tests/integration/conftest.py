"""Shared fixtures for integration tests."""

from __future__ import annotations

import os
import subprocess
import sys
from pathlib import Path

import pytest

REPO_ROOT = Path(__file__).resolve().parents[2]

_GIT_TEST_ENV = {
    **os.environ,
    "GIT_AUTHOR_NAME": "t",
    "GIT_AUTHOR_EMAIL": "t@t",
    "GIT_COMMITTER_NAME": "t",
    "GIT_COMMITTER_EMAIL": "t@t",
}


def run_claude_cli(
    args: list[str],
    *,
    cwd: Path | str | None = None,
    env: dict[str, str] | None = None,
    timeout: float = 120.0,
) -> subprocess.CompletedProcess[str]:
    """Invoke the Typer CLI in a subprocess with PYTHONPATH set to ``src``."""
    code = f"""import sys
sys.argv = ["claude"] + {args!r}
from claude_code.cli.main import main
main()
"""
    merged = {**os.environ, "PYTHONPATH": str(REPO_ROOT / "src")}
    if env:
        merged.update(env)
    return subprocess.run(
        [sys.executable, "-c", code],
        cwd=str(cwd or REPO_ROOT),
        capture_output=True,
        text=True,
        env=merged,
        timeout=timeout,
    )


@pytest.fixture
def isolated_claude_config(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> Path:
    """Point global config at ``tmp_path`` and clear the config-home cache."""
    import claude_code.utils.env_utils as env_utils

    monkeypatch.setenv("CLAUDE_CONFIG_DIR", str(tmp_path))
    env_utils.get_claude_config_home_dir.cache_clear()
    yield tmp_path
    env_utils.get_claude_config_home_dir.cache_clear()


@pytest.fixture
def git_repo(tmp_path: Path) -> Path:
    """Initialize a git repository under ``tmp_path``."""
    subprocess.run(
        ["git", "init"],
        cwd=tmp_path,
        capture_output=True,
        text=True,
        check=True,
        env=_GIT_TEST_ENV,
    )
    (tmp_path / "README.md").write_text("# hi\n", encoding="utf-8")
    subprocess.run(
        ["git", "add", "README.md"],
        cwd=tmp_path,
        capture_output=True,
        text=True,
        check=True,
    )
    subprocess.run(
        ["git", "commit", "-m", "init"],
        cwd=tmp_path,
        capture_output=True,
        text=True,
        check=True,
        env=_GIT_TEST_ENV,
    )
    return tmp_path
