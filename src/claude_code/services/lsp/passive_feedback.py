"""Map LSP diagnostics to Claude attachment format.

Migrated from: services/lsp/passiveFeedback.ts (core helpers).
"""

from __future__ import annotations

import os
from dataclasses import dataclass
from typing import Any, Literal
from urllib.parse import unquote, urlparse

from ..diagnostics.tracking import Diagnostic, DiagnosticFile, DiagnosticRange

Severity = Literal["Error", "Warning", "Info", "Hint"]


def map_lsp_severity(lsp_severity: int | None) -> Severity:
    if lsp_severity == 1:
        return "Error"
    if lsp_severity == 2:
        return "Warning"
    if lsp_severity == 3:
        return "Info"
    if lsp_severity == 4:
        return "Hint"
    return "Error"


def _uri_to_path(uri: str) -> str:
    if uri.startswith("file://"):
        parsed = urlparse(uri)
        path = unquote(parsed.path)
        if os.name == "nt" and path.startswith("/") and len(path) > 2 and path[2] == ":":
            return path[1:]
        return path
    return uri


def format_diagnostics_for_attachment(params: dict[str, Any]) -> list[DiagnosticFile]:
    uri_raw = params.get("uri", "")
    if not isinstance(uri_raw, str):
        return []
    try:
        path = _uri_to_path(uri_raw)
    except Exception:
        path = uri_raw
    diags_raw = params.get("diagnostics", [])
    if not isinstance(diags_raw, list):
        return []
    diagnostics: list[Diagnostic] = []
    for d in diags_raw:
        if not isinstance(d, dict):
            continue
        msg = d.get("message", "")
        if not isinstance(msg, str):
            continue
        rng = d.get("range", {})
        if not isinstance(rng, dict):
            continue
        start = rng.get("start", {})
        end = rng.get("end", {})
        if not isinstance(start, dict) or not isinstance(end, dict):
            continue
        code = d.get("code")
        code_s = str(code) if code is not None else None
        sev = d.get("severity")
        sev_i = int(sev) if isinstance(sev, (int, float)) else None
        diagnostics.append(
            Diagnostic(
                message=msg,
                severity=map_lsp_severity(sev_i),
                range=DiagnosticRange(
                    start_line=int(start.get("line", 0)),
                    start_character=int(start.get("character", 0)),
                    end_line=int(end.get("line", 0)),
                    end_character=int(end.get("character", 0)),
                ),
                source=d.get("source") if isinstance(d.get("source"), str) else None,
                code=code_s,
            )
        )
    return [DiagnosticFile(uri=path, diagnostics=diagnostics)]


@dataclass
class PublishDiagnosticsParams:
    uri: str
    diagnostics: list[dict[str, Any]]
