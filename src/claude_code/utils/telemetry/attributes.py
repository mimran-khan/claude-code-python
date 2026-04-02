"""
Resource / session attributes attached to telemetry events and spans.

Migrated from: utils/telemetryAttributes.ts (subset used by telemetry/events).
"""

from __future__ import annotations

import os
import platform
import sys
from functools import cache
from importlib import metadata
from typing import Any

from ...bootstrap.state import get_session_id


@cache
def _package_version() -> str:
    try:
        return metadata.version("claude-code")
    except metadata.PackageNotFoundError:
        return "unknown"


def get_telemetry_attributes() -> dict[str, Any]:
    """
    Base attributes merged into OTEL events and spans.

    Mirrors the TS ``getTelemetryAttributes()`` shape where applicable.
    """
    sid = get_session_id()
    attrs: dict[str, Any] = {
        "session.id": str(sid),
        "service.name": "claude-code",
        "service.version": _package_version(),
        "os.type": sys.platform,
        "python.version": platform.python_version(),
    }
    user_type = os.environ.get("USER_TYPE")
    if user_type:
        attrs["user.type"] = user_type
    return attrs
