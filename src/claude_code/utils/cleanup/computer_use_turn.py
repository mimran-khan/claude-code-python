"""
Turn-end cleanup for Computer Use MCP (unhide + lock + esc hotkey).

Delegates to ``claude_code.utils.computer_use.cleanup``.
"""

from __future__ import annotations

from ..computer_use.cleanup import cleanup_computer_use_after_turn

__all__ = ["cleanup_computer_use_after_turn"]
