"""
Format LSP locations and symbols for tool output.

Migrated from: tools/LSPTool/formatters.ts (subset — no vscode-languageserver-types dependency).
"""

from __future__ import annotations

import contextlib
import os
from urllib.parse import unquote


def format_uri(uri: str | None, cwd: str | None = None) -> str:
    if not uri:
        return "<unknown location>"
    file_path = uri.replace("file://", "", 1)
    if len(file_path) >= 3 and file_path[0] == "/" and file_path[2] == ":":
        file_path = file_path[1:]
    with contextlib.suppress(Exception):
        file_path = unquote(file_path)
    if cwd:
        try:
            rel = os.path.relpath(file_path, cwd).replace("\\", "/")
            if not rel.startswith("../"):
                return rel
        except ValueError:
            pass
    return file_path.replace("\\", "/")


def plural(n: int, singular: str, plural_form: str | None = None) -> str:
    p = plural_form or f"{singular}s"
    return f"{n} {singular}" if n == 1 else f"{n} {p}"


__all__ = ["format_uri", "plural"]
