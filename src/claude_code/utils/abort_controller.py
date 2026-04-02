"""
AbortController helpers.

Migrated from: utils/abortController.ts
"""

from __future__ import annotations

import asyncio


def create_abort_controller() -> asyncio.Event:
    """
    Create a simple cancellation token as an asyncio.Event.

    When set, consumers should treat the operation as aborted.
    """
    return asyncio.Event()
