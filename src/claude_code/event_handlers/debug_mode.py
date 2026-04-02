"""
Debug mode snapshot (ported from components/LogoV2 and utils/debug.ts usage).

Replaces render-time isDebugMode() checks with a small handler for status lines.
"""

from __future__ import annotations

from dataclasses import dataclass

from claude_code.utils.debug import (
    get_debug_file_path,
    is_debug_mode,
    is_debug_to_stderr,
)


@dataclass
class DebugModeHandler:
    """Lazily re-reads argv/env-backed debug flags when refresh() is called."""

    active: bool = False
    log_to_stderr: bool = False
    debug_file: str | None = None

    def refresh(self) -> None:
        self.active = is_debug_mode()
        self.log_to_stderr = is_debug_to_stderr()
        self.debug_file = get_debug_file_path()
