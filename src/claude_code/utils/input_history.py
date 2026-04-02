"""
REPL input history helpers (readline-backed).

Migrated from: utils/inputHistory.ts (source not in workspace; complements root input_history).
"""

from __future__ import annotations

import atexit
import os
import readline
from pathlib import Path


def get_history_path() -> Path:
    base = Path(os.environ.get("CLAUDE_CONFIG_DIR", Path.home() / ".claude"))
    base.mkdir(parents=True, exist_ok=True)
    return base / "repl_history"


def load_input_history(max_lines: int = 2000) -> None:
    """Load prior REPL lines into readline."""
    path = get_history_path()
    if path.is_file():
        try:
            readline.read_history_file(path)
            if readline.get_current_history_length() > max_lines:
                readline.remove_history_item(0)
        except OSError:
            pass


def append_input_history(line: str) -> None:
    """Append a non-empty line to readline history."""
    if line.strip():
        readline.add_history(line)


def save_input_history() -> None:
    """Persist readline history to disk."""
    path = get_history_path()
    try:
        path.parent.mkdir(parents=True, exist_ok=True)
        readline.write_history_file(path)
    except OSError:
        pass


def register_history_autosave() -> None:
    """Register atexit hook to save history."""

    def _flush() -> None:
        save_input_history()

    atexit.register(_flush)
