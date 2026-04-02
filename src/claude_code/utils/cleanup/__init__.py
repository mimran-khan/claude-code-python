"""
On-disk cleanup for logs, sessions, caches.

Migrated from: utils/cleanup.ts (core types and helpers).
"""

from .computer_use_turn import cleanup_computer_use_after_turn
from .core import (
    CleanupResult,
    add_cleanup_results,
    convert_file_name_to_date,
)

__all__ = [
    "CleanupResult",
    "add_cleanup_results",
    "cleanup_computer_use_after_turn",
    "convert_file_name_to_date",
]
