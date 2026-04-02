"""
LSP diagnostics.

Diagnostic tracking and management.

Migrated from: services/lsp/LSPDiagnosticRegistry.ts
"""

from __future__ import annotations

from dataclasses import dataclass, field
from enum import IntEnum
from typing import Any


class DiagnosticSeverity(IntEnum):
    """Severity levels for diagnostics."""

    ERROR = 1
    WARNING = 2
    INFORMATION = 3
    HINT = 4


@dataclass
class Position:
    """A position in a text document."""

    line: int
    character: int


@dataclass
class Range:
    """A range in a text document."""

    start: Position
    end: Position


@dataclass
class Diagnostic:
    """A diagnostic message."""

    range: Range
    message: str
    severity: DiagnosticSeverity = DiagnosticSeverity.ERROR
    code: str | None = None
    source: str | None = None
    related_information: list[Any] = field(default_factory=list)

    @staticmethod
    def from_dict(data: dict[str, Any]) -> Diagnostic:
        """Create from LSP diagnostic dict."""
        range_data = data.get("range", {})
        start = range_data.get("start", {})
        end = range_data.get("end", {})

        return Diagnostic(
            range=Range(
                start=Position(
                    line=start.get("line", 0),
                    character=start.get("character", 0),
                ),
                end=Position(
                    line=end.get("line", 0),
                    character=end.get("character", 0),
                ),
            ),
            message=data.get("message", ""),
            severity=DiagnosticSeverity(data.get("severity", 1)),
            code=data.get("code"),
            source=data.get("source"),
        )


class DiagnosticRegistry:
    """
    Registry for tracking diagnostics per file.
    """

    def __init__(self):
        self._diagnostics: dict[str, list[Diagnostic]] = {}

    def set_diagnostics(self, uri: str, diagnostics: list[Diagnostic]) -> None:
        """
        Set diagnostics for a file.

        Args:
            uri: File URI
            diagnostics: List of diagnostics
        """
        self._diagnostics[uri] = diagnostics

    def get_diagnostics(self, uri: str) -> list[Diagnostic]:
        """
        Get diagnostics for a file.

        Args:
            uri: File URI

        Returns:
            List of diagnostics
        """
        return self._diagnostics.get(uri, [])

    def clear_diagnostics(self, uri: str) -> None:
        """
        Clear diagnostics for a file.

        Args:
            uri: File URI
        """
        if uri in self._diagnostics:
            del self._diagnostics[uri]

    def clear_all(self) -> None:
        """Clear all diagnostics."""
        self._diagnostics.clear()

    def get_all_errors(self) -> dict[str, list[Diagnostic]]:
        """
        Get all error-level diagnostics.

        Returns:
            Dict mapping URIs to error diagnostics
        """
        result = {}
        for uri, diagnostics in self._diagnostics.items():
            errors = [d for d in diagnostics if d.severity == DiagnosticSeverity.ERROR]
            if errors:
                result[uri] = errors
        return result

    def get_error_count(self) -> int:
        """Get total error count."""
        count = 0
        for diagnostics in self._diagnostics.values():
            count += sum(1 for d in diagnostics if d.severity == DiagnosticSeverity.ERROR)
        return count

    def get_warning_count(self) -> int:
        """Get total warning count."""
        count = 0
        for diagnostics in self._diagnostics.values():
            count += sum(1 for d in diagnostics if d.severity == DiagnosticSeverity.WARNING)
        return count


# Global registry
_registry = DiagnosticRegistry()


def get_diagnostics_for_file(file_path: str) -> list[Diagnostic]:
    """
    Get diagnostics for a file.

    Args:
        file_path: File path

    Returns:
        List of diagnostics
    """
    uri = f"file://{file_path}"
    return _registry.get_diagnostics(uri)
