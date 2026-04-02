"""
Terminal input tokenization (escape-sequence boundaries).

TS sources: `ink/termio/tokenize.ts` (not under `utils/`). Use a dedicated
TUI library or extend this module with a small state machine when wiring stdin.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Literal

TokenType = Literal["text", "sequence"]


@dataclass(frozen=True, slots=True)
class TerminalToken:
    type: TokenType
    value: str


def tokenize_terminal_input_chunk(chunk: str) -> list[TerminalToken]:
    """
    Split on ESC starts only (minimal): full CSI/state machine not implemented.
    """
    if "\x1b" not in chunk:
        return [TerminalToken("text", chunk)]
    out: list[TerminalToken] = []
    parts = chunk.split("\x1b")
    if parts[0]:
        out.append(TerminalToken("text", parts[0]))
    for p in parts[1:]:
        out.append(TerminalToken("sequence", "\x1b" + p))
    return out
