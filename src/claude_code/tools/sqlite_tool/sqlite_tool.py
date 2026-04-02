"""
Read-only SQLite query tool.

Python counterpart for SqliteTool / MCP read_query patterns (no TS in leak).
"""

from __future__ import annotations

import re
import sqlite3
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from ..base import Tool, ToolResult, ToolUseContext
from .constants import SQLITE_TOOL_NAME
from .prompt_text import DESCRIPTION, PROMPT

_READ_ONLY_RE = re.compile(
    r"^\s*(with|select)\b",
    re.IGNORECASE | re.DOTALL,
)


@dataclass
class SqliteInput:
    db_path: str
    query: str


@dataclass
class SqliteOutput:
    columns: list[str]
    rows: list[list[Any]]
    row_count: int


class SqliteTool(Tool[dict[str, Any], SqliteOutput]):
    @property
    def name(self) -> str:
        return SQLITE_TOOL_NAME

    @property
    def search_hint(self) -> str:
        return "sqlite read query"

    async def description(self) -> str:
        return DESCRIPTION

    async def prompt(self) -> str:
        return PROMPT

    def get_input_schema(self) -> dict[str, Any]:
        return {
            "type": "object",
            "properties": {
                "db_path": {"type": "string"},
                "query": {"type": "string"},
            },
            "required": ["db_path", "query"],
        }

    def get_output_schema(self) -> dict[str, Any]:
        return {
            "type": "object",
            "properties": {
                "columns": {"type": "array", "items": {"type": "string"}},
                "rows": {"type": "array"},
                "row_count": {"type": "integer"},
            },
        }

    async def execute(
        self,
        input: dict[str, Any],
        context: ToolUseContext,
    ) -> ToolResult:
        db_path = str(input.get("db_path", "")).strip()
        query = str(input.get("query", "")).strip()
        if not db_path or not query:
            return ToolResult(success=False, error="db_path and query are required", error_code=1)
        if not _READ_ONLY_RE.match(query):
            return ToolResult(
                success=False,
                error="Only read-only SELECT or WITH queries are allowed",
                error_code=1,
            )
        forbidden = re.compile(
            r"\b(insert|update|delete|drop|alter|create|attach|pragma|replace)\b",
            re.IGNORECASE,
        )
        if forbidden.search(query):
            return ToolResult(
                success=False,
                error="Mutating or pragma statements are not allowed",
                error_code=1,
            )

        p = Path(db_path).resolve()
        cwd = Path(context.get_cwd()).resolve()
        try:
            p.relative_to(cwd)
        except ValueError:
            return ToolResult(
                success=False,
                error="Database path must be under the current working directory",
                error_code=1,
            )
        if not p.is_file():
            return ToolResult(success=False, error=f"Database not found: {p}", error_code=1)

        try:
            con = sqlite3.connect(f"file:{p}?mode=ro", uri=True)
            try:
                cur = con.execute(query)
                columns = [d[0] for d in cur.description] if cur.description else []
                rows = cur.fetchmany(500)
                row_count = len(rows)
            finally:
                con.close()
        except sqlite3.Error as e:
            return ToolResult(success=False, error=str(e), error_code=1)

        return ToolResult(
            success=True,
            output=SqliteOutput(columns=columns, rows=[list(r) for r in rows], row_count=row_count),
        )
