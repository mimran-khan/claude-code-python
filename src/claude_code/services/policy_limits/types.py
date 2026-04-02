"""Policy limits API types. Migrated from: services/policyLimits/types.ts"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any


@dataclass
class PolicyRestriction:
    allowed: bool


PolicyRestrictions = dict[str, PolicyRestriction]


def parse_policy_limits_payload(data: Any) -> dict[str, PolicyRestriction] | None:
    if not isinstance(data, dict):
        return None
    raw = data.get("restrictions")
    if not isinstance(raw, dict):
        return None
    out: dict[str, PolicyRestriction] = {}
    for k, v in raw.items():
        if not isinstance(k, str) or not isinstance(v, dict):
            return None
        if "allowed" not in v or not isinstance(v["allowed"], bool):
            return None
        out[k] = PolicyRestriction(allowed=v["allowed"])
    return out


@dataclass
class PolicyLimitsFetchResult:
    success: bool
    restrictions: dict[str, PolicyRestriction] | None = None
    etag: str | None = None
    error: str | None = None
    skip_retry: bool = False
