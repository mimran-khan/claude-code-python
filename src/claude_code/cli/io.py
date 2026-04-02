"""
CLI input/output.

Structured and remote I/O handling.

Migrated from: cli/structuredIO.ts + remoteIO.ts
"""

from __future__ import annotations

import json
import sys
from collections.abc import Callable
from dataclasses import dataclass, field
from typing import Any, TextIO


@dataclass
class StructuredIO:
    """
    Structured I/O for non-interactive mode.

    Outputs JSON-formatted messages.
    """

    output: TextIO = field(default_factory=lambda: sys.stdout)
    input: TextIO = field(default_factory=lambda: sys.stdin)

    def write_message(self, msg_type: str, data: Any) -> None:
        """
        Write a structured message.

        Args:
            msg_type: Message type
            data: Message data
        """
        message = {
            "type": msg_type,
            "data": data,
        }
        self.output.write(json.dumps(message) + "\n")
        self.output.flush()

    def write_error(self, error: str, code: int = 1) -> None:
        """Write an error message."""
        self.write_message("error", {"message": error, "code": code})

    def write_result(self, result: Any) -> None:
        """Write a result message."""
        self.write_message("result", result)

    def write_progress(self, message: str, progress: float | None = None) -> None:
        """Write a progress message."""
        data = {"message": message}
        if progress is not None:
            data["progress"] = progress
        self.write_message("progress", data)

    def read_message(self) -> dict[str, Any] | None:
        """
        Read a structured message.

        Returns:
            Parsed message or None
        """
        try:
            line = self.input.readline()
            if not line:
                return None
            return json.loads(line)
        except json.JSONDecodeError:
            return None


@dataclass
class RemoteIO:
    """
    Remote I/O for WebSocket/SSE communication.
    """

    send: Callable[[dict[str, Any]], None] | None = None
    receive: Callable[[], dict[str, Any] | None] | None = None

    def write_message(self, msg_type: str, data: Any) -> None:
        """Write a message to remote."""
        if self.send:
            self.send({"type": msg_type, "data": data})

    def write_error(self, error: str, code: int = 1) -> None:
        """Write an error message."""
        self.write_message("error", {"message": error, "code": code})

    def write_result(self, result: Any) -> None:
        """Write a result message."""
        self.write_message("result", result)

    def read_message(self) -> dict[str, Any] | None:
        """Read a message from remote."""
        if self.receive:
            return self.receive()
        return None


def write_to_stdout(message: str, newline: bool = True) -> None:
    """
    Write to stdout.

    Args:
        message: Message to write
        newline: Whether to add newline
    """
    sys.stdout.write(message)
    if newline:
        sys.stdout.write("\n")
    sys.stdout.flush()


def read_from_stdin(prompt: str = "") -> str:
    """
    Read from stdin.

    Args:
        prompt: Optional prompt to display

    Returns:
        Input string
    """
    if prompt:
        sys.stdout.write(prompt)
        sys.stdout.flush()
    return sys.stdin.readline().rstrip("\n")


def ndjson_safe_stringify(obj: Any) -> str:
    """
    Stringify object for NDJSON output.

    Ensures no newlines in output.

    Args:
        obj: Object to stringify

    Returns:
        JSON string without embedded newlines
    """
    return json.dumps(obj, separators=(",", ":"))
