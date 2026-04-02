"""
Shell Configuration Utilities.

Utilities for managing shell configuration files (like .bashrc, .zshrc).
Used for managing claude aliases and PATH entries.
"""

from __future__ import annotations

import os
import re
from pathlib import Path

CLAUDE_ALIAS_REGEX = re.compile(r"^\s*alias\s+claude\s*=")


def get_shell_config_paths(
    *,
    env: dict[str, str] | None = None,
    homedir: str | None = None,
) -> dict[str, str]:
    """Get the paths to shell configuration files.

    Respects ZDOTDIR for zsh users.

    Args:
        env: Optional environment dict override for testing
        homedir: Optional home directory override for testing

    Returns:
        Dict mapping shell name to config path
    """
    home = homedir or str(Path.home())
    env = env or dict(os.environ)
    zsh_config_dir = env.get("ZDOTDIR", home)

    return {
        "zsh": os.path.join(zsh_config_dir, ".zshrc"),
        "bash": os.path.join(home, ".bashrc"),
        "fish": os.path.join(home, ".config/fish/config.fish"),
    }


def get_local_claude_path() -> str:
    """Get the path to locally installed claude."""
    return os.path.join(str(Path.home()), ".claude", "local", "claude")


def filter_claude_aliases(lines: list[str]) -> tuple[list[str], bool]:
    """Filter out installer-created claude aliases from lines.

    Only removes aliases pointing to $HOME/.claude/local/claude.
    Preserves custom user aliases that point to other locations.

    Args:
        lines: List of lines from config file

    Returns:
        Tuple of (filtered lines, whether our default alias was found)
    """
    had_alias = False
    filtered = []
    local_path = get_local_claude_path()

    for line in lines:
        if CLAUDE_ALIAS_REGEX.search(line):
            # Extract the alias target
            match = re.search(r'alias\s+claude\s*=\s*["\']?([^"\']+)["\']?', line)
            if match:
                target = match.group(1).strip()
                if target == local_path:
                    had_alias = True
                    continue  # Skip this line
        filtered.append(line)

    return filtered, had_alias


async def read_file_lines(file_path: str) -> list[str] | None:
    """Read a file and split it into lines.

    Args:
        file_path: Path to the file

    Returns:
        List of lines, or None if file doesn't exist
    """
    try:
        with open(file_path, encoding="utf-8") as f:
            return f.read().split("\n")
    except (FileNotFoundError, PermissionError):
        return None


async def write_file_lines(file_path: str, lines: list[str]) -> None:
    """Write lines back to a file.

    Args:
        file_path: Path to the file
        lines: Lines to write
    """
    with open(file_path, "w", encoding="utf-8") as f:
        f.write("\n".join(lines))
        f.flush()
        os.fsync(f.fileno())


async def find_claude_alias(
    *,
    env: dict[str, str] | None = None,
    homedir: str | None = None,
) -> str | None:
    """Check if a claude alias exists in any shell config file.

    Args:
        env: Optional environment dict override
        homedir: Optional home directory override

    Returns:
        The alias target if found, None otherwise
    """
    configs = get_shell_config_paths(env=env, homedir=homedir)

    for config_path in configs.values():
        lines = await read_file_lines(config_path)
        if not lines:
            continue

        for line in lines:
            if CLAUDE_ALIAS_REGEX.search(line):
                match = re.search(r"alias\s+claude=[\"']?([^\"'\s]+)", line)
                if match:
                    return match.group(1)

    return None


async def find_valid_claude_alias(
    *,
    env: dict[str, str] | None = None,
    homedir: str | None = None,
) -> str | None:
    """Check if a claude alias exists and points to a valid executable.

    Args:
        env: Optional environment dict override
        homedir: Optional home directory override

    Returns:
        The alias target if valid, None otherwise
    """
    alias_target = await find_claude_alias(env=env, homedir=homedir)
    if not alias_target:
        return None

    home = homedir or str(Path.home())

    # Expand ~ to home directory
    expanded_path = alias_target.replace("~", home, 1) if alias_target.startswith("~") else alias_target

    # Check if the target exists
    path = Path(expanded_path)
    if path.is_file() or path.is_symlink():
        return alias_target

    return None
