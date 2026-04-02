"""
Shell history suggestions.

Migrated from: utils/suggestions/shellHistoryCompletion.ts
"""

from __future__ import annotations

import os


def load_shell_history(
    shell: str | None = None,
    max_entries: int = 1000,
) -> list[str]:
    """
    Load shell command history.

    Args:
        shell: Shell type (bash, zsh, fish)
        max_entries: Maximum entries to load

    Returns:
        List of history commands
    """
    if shell is None:
        shell = os.path.basename(os.getenv("SHELL", "bash"))

    home = os.path.expanduser("~")
    history_files = {
        "bash": [".bash_history"],
        "zsh": [".zsh_history", ".zhistory"],
        "fish": [".local/share/fish/fish_history"],
    }

    files = history_files.get(shell, [".bash_history"])

    history: list[str] = []

    for file in files:
        path = os.path.join(home, file)
        if os.path.exists(path):
            try:
                with open(path, errors="ignore") as f:
                    lines = f.readlines()

                # Parse based on shell format
                if shell == "zsh":
                    history.extend(_parse_zsh_history(lines))
                elif shell == "fish":
                    history.extend(_parse_fish_history(lines))
                else:
                    history.extend(_parse_bash_history(lines))

                break  # Use first found file

            except (OSError, PermissionError):
                continue

    # Return most recent entries
    return history[-max_entries:]


def _parse_bash_history(lines: list[str]) -> list[str]:
    """Parse bash history format."""
    return [line.strip() for line in lines if line.strip()]


def _parse_zsh_history(lines: list[str]) -> list[str]:
    """Parse zsh history format (extended history)."""
    commands: list[str] = []

    for line in lines:
        line = line.strip()
        if not line:
            continue

        # Extended history format: : timestamp:duration;command
        if line.startswith(":"):
            parts = line.split(";", 1)
            if len(parts) > 1:
                commands.append(parts[1])
        else:
            commands.append(line)

    return commands


def _parse_fish_history(lines: list[str]) -> list[str]:
    """Parse fish history format (YAML-like)."""
    commands: list[str] = []

    for line in lines:
        line = line.strip()
        if line.startswith("- cmd:"):
            cmd = line[6:].strip()
            commands.append(cmd)

    return commands


def get_shell_history_suggestions(
    query: str,
    shell: str | None = None,
    max_results: int = 10,
) -> list[str]:
    """
    Get suggestions from shell history.

    Args:
        query: Search query
        shell: Shell type
        max_results: Maximum results

    Returns:
        Matching history commands
    """
    history = load_shell_history(shell)
    query = query.lower()

    # Find matching commands
    matches: list[str] = []
    seen: set[str] = set()

    # Search from most recent
    for cmd in reversed(history):
        if query in cmd.lower() and cmd not in seen:
            seen.add(cmd)
            matches.append(cmd)

            if len(matches) >= max_results:
                break

    return matches
