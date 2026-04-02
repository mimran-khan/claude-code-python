"""Event metadata enrichment."""

import os
import platform
from typing import Any


def get_event_metadata() -> dict[str, Any]:
    """Get base event metadata."""
    return {
        "platform": platform.system().lower(),
        "platform_version": platform.version(),
        "python_version": platform.python_version(),
        "user_type": os.environ.get("USER_TYPE", "external"),
    }


def enrich_metadata(
    metadata: dict[str, Any],
    extra: dict[str, Any] | None = None,
) -> dict[str, Any]:
    """Enrich metadata with base fields."""
    result = get_event_metadata()
    result.update(metadata)
    if extra:
        result.update(extra)
    return result
