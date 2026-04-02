"""Prompt for reading the current session todo list."""

from __future__ import annotations

DESCRIPTION = "Return the current session todo list from application state."

PROMPT = """
Read the active todo items (if any) from session state. Read-only; use TodoWrite to modify.
""".strip()
