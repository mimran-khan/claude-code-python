"""Shell completion cache generation and rc-file hooks."""

from __future__ import annotations

import asyncio
import os
import subprocess
from dataclasses import dataclass
from pathlib import Path


@dataclass
class ShellInfo:
    name: str
    rc_file: Path
    cache_file: Path
    completion_line: str
    shell_flag: str


def detect_shell() -> ShellInfo | None:
    shell = os.environ.get("SHELL") or ""
    home = Path.home()
    claude_dir = home / ".claude"

    if shell.endswith("/zsh") or shell.endswith("/zsh.exe"):
        cache_file = claude_dir / "completion.zsh"
        return ShellInfo(
            name="zsh",
            rc_file=home / ".zshrc",
            cache_file=cache_file,
            completion_line=f'[[ -f "{cache_file}" ]] && source "{cache_file}"',
            shell_flag="zsh",
        )
    if shell.endswith("/bash") or shell.endswith("/bash.exe"):
        cache_file = claude_dir / "completion.bash"
        return ShellInfo(
            name="bash",
            rc_file=home / ".bashrc",
            cache_file=cache_file,
            completion_line=f'[ -f "{cache_file}" ] && source "{cache_file}"',
            shell_flag="bash",
        )
    if shell.endswith("/fish") or shell.endswith("/fish.exe"):
        xdg = os.environ.get("XDG_CONFIG_HOME") or str(home / ".config")
        cache_file = claude_dir / "completion.fish"
        return ShellInfo(
            name="fish",
            rc_file=Path(xdg) / "fish" / "config.fish",
            cache_file=cache_file,
            completion_line=f'[ -f "{cache_file}" ] && source "{cache_file}"',
            shell_flag="fish",
        )
    return None


async def setup_shell_completion(_theme: str) -> str:
    """Generate completion script and append source line to the shell rc file."""
    shell = detect_shell()
    if shell is None:
        return ""

    shell.cache_file.parent.mkdir(parents=True, exist_ok=True)
    claude_bin = os.environ.get("CLAUDE_CODE_BIN") or "claude"
    try:
        proc = await asyncio.to_thread(
            subprocess.run,
            [
                claude_bin,
                "completion",
                shell.shell_flag,
                "--output",
                str(shell.cache_file),
            ],
            capture_output=True,
            text=True,
            timeout=120,
        )
        if proc.returncode != 0:
            return (
                f"\nCould not generate {shell.name} shell completions "
                f"(exit {proc.returncode}).\n"
                f"Run manually: {claude_bin} completion {shell.shell_flag} > {shell.cache_file}\n"
            )
    except (OSError, subprocess.TimeoutExpired) as e:
        return f"\nCould not write {shell.name} completion cache: {e}\n"

    existing = ""
    try:
        existing = shell.rc_file.read_text(encoding="utf-8")
        if "claude completion" in existing or str(shell.cache_file) in existing:
            return f"\nShell completions updated for {shell.name}.\nSee {shell.rc_file}\n"
    except OSError:
        pass

    try:
        shell.rc_file.parent.mkdir(parents=True, exist_ok=True)
        sep = "\n" if existing and not existing.endswith("\n") else ""
        block = f"{existing}{sep}\n# Claude Code shell completions\n{shell.completion_line}\n"
        shell.rc_file.write_text(block, encoding="utf-8")
        return f"\nInstalled {shell.name} shell completions.\nAdded to {shell.rc_file}\nRun: source {shell.rc_file}\n"
    except OSError as e:
        return (
            f"\nCould not install {shell.name} shell completions: {e}\n"
            f"Add this to {shell.rc_file}:\n{shell.completion_line}\n"
        )


async def regenerate_completion_cache() -> None:
    shell = detect_shell()
    if shell is None:
        return
    claude_bin = os.environ.get("CLAUDE_CODE_BIN") or "claude"
    try:
        proc = await asyncio.to_thread(
            subprocess.run,
            [
                claude_bin,
                "completion",
                shell.shell_flag,
                "--output",
                str(shell.cache_file),
            ],
            capture_output=True,
            text=True,
            timeout=120,
        )
        if proc.returncode != 0:
            return
    except (OSError, subprocess.TimeoutExpired):
        return
