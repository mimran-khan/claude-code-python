"""
Signal + combined cancellation exports (TS ``signal.ts`` + ``combinedAbortSignal.ts``).
"""

from __future__ import annotations

from .combined_abort_signal import create_combined_abort_signal
from .signal import Signal, VoidSignal, create_signal

__all__ = [
    "Signal",
    "VoidSignal",
    "create_combined_abort_signal",
    "create_signal",
]
