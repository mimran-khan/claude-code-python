"""Schema for permission updates (``PermissionUpdateSchema.ts``)."""

from __future__ import annotations

from typing import Any

PERMISSION_UPDATE_SCHEMA: dict[str, Any] = {
    "type": "object",
    "properties": {"action": {"type": "string"}, "rule": {"type": "object"}},
    "required": ["action"],
}
