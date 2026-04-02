"""
Test fixture record/replay (VCR-style) for API calls.

Migrated from: services/vcr.ts — minimal placeholder until full port.
"""

from __future__ import annotations

import inspect
import os
from collections.abc import Callable
from typing import Any, TypeVar

T = TypeVar("T")


def should_use_vcr() -> bool:
    if os.environ.get("NODE_ENV") == "test":
        return True
    return bool(
        os.environ.get("USER_TYPE") == "ant" and os.environ.get("FORCE_VCR", "").lower() in ("1", "true", "yes")
    )


async def with_fixture(
    _key: str,
    producer: Callable[[], Any],
    *,
    replay: bool | None = None,
) -> Any:
    """Run producer directly; disk fixtures not wired in this build."""
    _ = replay
    result = producer()
    if inspect.isawaitable(result):
        return await result  # type: ignore[no-any-return]
    return result
