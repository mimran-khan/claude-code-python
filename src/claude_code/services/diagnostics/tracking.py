"""
Diagnostic Tracking Service.

Tracks and compares diagnostics for files before and after edits.
"""

from __future__ import annotations

import os
from dataclasses import dataclass, field
from typing import Literal

MAX_DIAGNOSTICS_SUMMARY_CHARS = 4000


@dataclass
class DiagnosticRange:
    """Range of a diagnostic in a file."""

    start_line: int
    start_character: int
    end_line: int
    end_character: int


@dataclass
class Diagnostic:
    """A single diagnostic (error, warning, etc.)."""

    message: str
    severity: Literal["Error", "Warning", "Info", "Hint"]
    range: DiagnosticRange
    source: str | None = None
    code: str | None = None


@dataclass
class DiagnosticFile:
    """Diagnostics for a single file."""

    uri: str
    diagnostics: list[Diagnostic] = field(default_factory=list)


class DiagnosticTrackingService:
    """Service for tracking file diagnostics across edits."""

    _instance: DiagnosticTrackingService | None = None

    def __init__(self) -> None:
        self._baseline: dict[str, list[Diagnostic]] = {}
        self._initialized = False
        self._last_processed_timestamps: dict[str, float] = {}
        self._right_file_diagnostics_state: dict[str, list[Diagnostic]] = {}

    @classmethod
    def get_instance(cls) -> DiagnosticTrackingService:
        """Get the singleton instance."""
        if cls._instance is None:
            cls._instance = DiagnosticTrackingService()
        return cls._instance

    def initialize(self) -> None:
        """Initialize the service."""
        if self._initialized:
            return
        self._initialized = True

    async def shutdown(self) -> None:
        """Shutdown the service."""
        self._initialized = False
        self._baseline.clear()
        self._right_file_diagnostics_state.clear()
        self._last_processed_timestamps.clear()

    def reset(self) -> None:
        """Reset tracking state while keeping the service initialized."""
        self._baseline.clear()
        self._right_file_diagnostics_state.clear()
        self._last_processed_timestamps.clear()

    def _normalize_file_uri(self, file_uri: str) -> str:
        """Normalize a file URI for comparison."""
        # Remove protocol prefixes
        prefixes = ["file://", "_claude_fs_right:", "_claude_fs_left:"]

        normalized = file_uri
        for prefix in prefixes:
            if file_uri.startswith(prefix):
                normalized = file_uri[len(prefix) :]
                break

        # Normalize path for platform
        return os.path.normpath(normalized).lower()

    async def before_file_edited(self, file_path: str) -> None:
        """Capture baseline diagnostics for a file before editing.

        Args:
            file_path: Path to the file being edited
        """
        if not self._initialized:
            return

        import time

        timestamp = time.time()
        normalized_path = self._normalize_file_uri(file_path)

        # In a full implementation, this would fetch diagnostics from IDE
        # For now, just store an empty baseline
        self._baseline[normalized_path] = []
        self._last_processed_timestamps[normalized_path] = timestamp

    async def get_new_diagnostics(self) -> list[DiagnosticFile]:
        """Get new diagnostics that aren't in the baseline.

        Returns:
            List of diagnostic files with new diagnostics
        """
        if not self._initialized:
            return []

        # In a full implementation, this would:
        # 1. Fetch current diagnostics from IDE
        # 2. Compare against baseline
        # 3. Return only new diagnostics
        return []

    def _are_diagnostics_equal(self, a: Diagnostic, b: Diagnostic) -> bool:
        """Check if two diagnostics are equal."""
        return (
            a.message == b.message
            and a.severity == b.severity
            and a.source == b.source
            and a.code == b.code
            and a.range.start_line == b.range.start_line
            and a.range.start_character == b.range.start_character
            and a.range.end_line == b.range.end_line
            and a.range.end_character == b.range.end_character
        )

    @staticmethod
    def get_severity_symbol(severity: str) -> str:
        """Get the severity symbol for a diagnostic."""
        symbols = {
            "Error": "✘",
            "Warning": "⚠",
            "Info": "ℹ",
            "Hint": "★",
        }
        return symbols.get(severity, "•")

    @staticmethod
    def format_diagnostics_summary(files: list[DiagnosticFile]) -> str:
        """Format diagnostics into a human-readable summary string.

        Args:
            files: List of diagnostic files to format

        Returns:
            Formatted string representation
        """
        truncation_marker = "…[truncated]"

        parts = []
        for file in files:
            filename = os.path.basename(file.uri)
            diagnostics_str = "\n".join(
                f"  {DiagnosticTrackingService.get_severity_symbol(d.severity)} "
                f"[Line {d.range.start_line + 1}:{d.range.start_character + 1}] "
                f"{d.message}"
                f"{f' [{d.code}]' if d.code else ''}"
                f"{f' ({d.source})' if d.source else ''}"
                for d in file.diagnostics
            )
            parts.append(f"{filename}:\n{diagnostics_str}")

        result = "\n\n".join(parts)

        if len(result) > MAX_DIAGNOSTICS_SUMMARY_CHARS:
            return result[: MAX_DIAGNOSTICS_SUMMARY_CHARS - len(truncation_marker)] + truncation_marker

        return result


# Singleton instance
diagnostic_tracker = DiagnosticTrackingService.get_instance()
