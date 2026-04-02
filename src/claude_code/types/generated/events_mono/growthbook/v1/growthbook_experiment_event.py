"""
GrowthBook experiment assignment event schema.

Migrated from: types/generated/events_mono/growthbook/v1/growthbook_experiment_event.ts
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from typing import Any

from ....google.protobuf.timestamp import datetime_to_iso_z, parse_flexible_timestamp
from ...common.v1.auth import (
    PublicApiAuth,
    public_api_auth_from_json,
    public_api_auth_from_partial,
    public_api_auth_to_json,
)


@dataclass
class GrowthbookExperimentEvent:
    event_id: str = ""
    timestamp: datetime | None = None
    experiment_id: str = ""
    variation_id: int = 0
    environment: str = ""
    user_attributes: str = ""
    experiment_metadata: str = ""
    device_id: str = ""
    auth: PublicApiAuth | None = None
    session_id: str = ""
    anonymous_id: str = ""
    event_metadata_vars: str = ""


def _is_set(value: Any) -> bool:
    return value is not None


def growthbook_experiment_event_from_json(obj: Any) -> GrowthbookExperimentEvent:
    if not isinstance(obj, dict):
        return GrowthbookExperimentEvent()
    ts_raw = obj.get("timestamp")
    return GrowthbookExperimentEvent(
        event_id=str(obj["event_id"]) if _is_set(obj.get("event_id")) else "",
        timestamp=parse_flexible_timestamp(ts_raw) if _is_set(ts_raw) else None,
        experiment_id=str(obj["experiment_id"]) if _is_set(obj.get("experiment_id")) else "",
        variation_id=int(obj["variation_id"]) if _is_set(obj.get("variation_id")) else 0,
        environment=str(obj["environment"]) if _is_set(obj.get("environment")) else "",
        user_attributes=str(obj["user_attributes"]) if _is_set(obj.get("user_attributes")) else "",
        experiment_metadata=str(obj["experiment_metadata"]) if _is_set(obj.get("experiment_metadata")) else "",
        device_id=str(obj["device_id"]) if _is_set(obj.get("device_id")) else "",
        auth=public_api_auth_from_json(obj["auth"]) if _is_set(obj.get("auth")) else None,
        session_id=str(obj["session_id"]) if _is_set(obj.get("session_id")) else "",
        anonymous_id=str(obj["anonymous_id"]) if _is_set(obj.get("anonymous_id")) else "",
        event_metadata_vars=str(obj["event_metadata_vars"]) if _is_set(obj.get("event_metadata_vars")) else "",
    )


def growthbook_experiment_event_to_json(message: GrowthbookExperimentEvent) -> dict[str, Any]:
    obj: dict[str, Any] = {}
    if message.event_id:
        obj["event_id"] = message.event_id
    if message.timestamp is not None:
        obj["timestamp"] = datetime_to_iso_z(message.timestamp)
    if message.experiment_id:
        obj["experiment_id"] = message.experiment_id
    if message.variation_id != 0:
        obj["variation_id"] = int(round(message.variation_id))
    if message.environment:
        obj["environment"] = message.environment
    if message.user_attributes:
        obj["user_attributes"] = message.user_attributes
    if message.experiment_metadata:
        obj["experiment_metadata"] = message.experiment_metadata
    if message.device_id:
        obj["device_id"] = message.device_id
    if message.auth is not None:
        obj["auth"] = public_api_auth_to_json(message.auth)
    if message.session_id:
        obj["session_id"] = message.session_id
    if message.anonymous_id:
        obj["anonymous_id"] = message.anonymous_id
    if message.event_metadata_vars:
        obj["event_metadata_vars"] = message.event_metadata_vars
    return obj


def growthbook_experiment_event_from_partial(obj: Any) -> GrowthbookExperimentEvent:
    if not isinstance(obj, dict):
        return GrowthbookExperimentEvent()
    auth_raw = obj.get("auth")
    return GrowthbookExperimentEvent(
        event_id=str(obj.get("event_id", "") or ""),
        timestamp=parse_flexible_timestamp(obj.get("timestamp")) if obj.get("timestamp") is not None else None,
        experiment_id=str(obj.get("experiment_id", "") or ""),
        variation_id=int(obj.get("variation_id", 0) or 0),
        environment=str(obj.get("environment", "") or ""),
        user_attributes=str(obj.get("user_attributes", "") or ""),
        experiment_metadata=str(obj.get("experiment_metadata", "") or ""),
        device_id=str(obj.get("device_id", "") or ""),
        auth=public_api_auth_from_partial(auth_raw) if isinstance(auth_raw, dict) else None,
        session_id=str(obj.get("session_id", "") or ""),
        anonymous_id=str(obj.get("anonymous_id", "") or ""),
        event_metadata_vars=str(obj.get("event_metadata_vars", "") or ""),
    )
