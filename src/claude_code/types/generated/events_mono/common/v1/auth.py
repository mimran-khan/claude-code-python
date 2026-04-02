"""
Public API authentication context on analytics events.

Migrated from: types/generated/events_mono/common/v1/auth.ts
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any


@dataclass
class PublicApiAuth:
    account_id: int = 0
    organization_uuid: str = ""
    account_uuid: str = ""


def _is_set(value: Any) -> bool:
    return value is not None


def public_api_auth_from_json(obj: Any) -> PublicApiAuth:
    if not isinstance(obj, dict):
        return PublicApiAuth()
    return PublicApiAuth(
        account_id=int(obj["account_id"]) if _is_set(obj.get("account_id")) else 0,
        organization_uuid=str(obj["organization_uuid"]) if _is_set(obj.get("organization_uuid")) else "",
        account_uuid=str(obj["account_uuid"]) if _is_set(obj.get("account_uuid")) else "",
    )


def public_api_auth_to_json(message: PublicApiAuth) -> dict[str, Any]:
    return {
        "account_id": int(round(message.account_id)),
        "organization_uuid": message.organization_uuid,
        "account_uuid": message.account_uuid,
    }


def public_api_auth_from_partial(obj: Any) -> PublicApiAuth:
    if not isinstance(obj, dict):
        return PublicApiAuth()
    return PublicApiAuth(
        account_id=int(obj.get("account_id", 0) or 0),
        organization_uuid=str(obj.get("organization_uuid", "") or ""),
        account_uuid=str(obj.get("account_uuid", "") or ""),
    )
