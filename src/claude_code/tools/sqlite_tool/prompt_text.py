"""Prompt for read-only SQLite access."""

from __future__ import annotations

DESCRIPTION = (
    "Run a read-only SQL query against a local SQLite database file (SELECT / WITH only; mutating statements rejected)."
)

PROMPT = """
Execute a single read-only statement against the database at db_path.
Only SELECT or WITH queries are allowed. Path must be under the project cwd.
""".strip()
