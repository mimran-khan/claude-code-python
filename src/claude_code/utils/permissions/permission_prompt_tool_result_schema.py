"""JSON schema for permission tool results (``PermissionPromptToolResultSchema.ts``)."""

from __future__ import annotations

from typing import Any

PERMISSION_PROMPT_TOOL_RESULT_SCHEMA: dict[str, Any] = {
    "type": "object",
    "properties": {
        "decision": {"type": "string"},
        "rule_id": {"type": "string"},
    },
    "additionalProperties": True,
}
