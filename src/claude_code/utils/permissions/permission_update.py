"""Permission rule updates (``utils/permissions/PermissionUpdate.ts``) — stub."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any


@dataclass
class PermissionUpdate:
    action: str
    rule: dict[str, Any]
