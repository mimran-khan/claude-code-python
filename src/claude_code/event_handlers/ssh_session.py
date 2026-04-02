"""
SSH child session bridge (same REPL shape as remote).

Migrated from: hooks/useSSHSession.ts
"""

from __future__ import annotations

from collections.abc import Callable
from dataclasses import dataclass
from typing import Any


@dataclass
class SshSessionHandles:
    send_message: Callable[[Any], Any]
    cancel_request: Callable[[], None]
    disconnect: Callable[[], None]
