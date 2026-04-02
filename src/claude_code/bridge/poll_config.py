"""GrowthBook-backed poll interval config with Pydantic validation."""

from __future__ import annotations

from dataclasses import asdict
from typing import Any

from pydantic import BaseModel, Field, model_validator

from claude_code.bridge.poll_config_defaults import DEFAULT_POLL_CONFIG, PollIntervalConfig


class _PollIntervalConfigModel(BaseModel):
    """Zod-equivalent validation for tengu_bridge_poll_interval_config."""

    poll_interval_ms_not_at_capacity: int = Field(ge=100)
    poll_interval_ms_at_capacity: int
    non_exclusive_heartbeat_interval_ms: int = Field(default=0, ge=0)
    multisession_poll_interval_ms_not_at_capacity: int = Field(
        default=DEFAULT_POLL_CONFIG.multisession_poll_interval_ms_not_at_capacity, ge=100
    )
    multisession_poll_interval_ms_partial_capacity: int = Field(
        default=DEFAULT_POLL_CONFIG.multisession_poll_interval_ms_partial_capacity, ge=100
    )
    multisession_poll_interval_ms_at_capacity: int = Field(
        default=DEFAULT_POLL_CONFIG.multisession_poll_interval_ms_at_capacity
    )
    reclaim_older_than_ms: int = Field(default=5000, ge=1)
    session_keepalive_interval_v2_ms: int = Field(default=120_000, ge=0)

    @staticmethod
    def _zero_or_ge_100(v: int) -> bool:
        return v == 0 or v >= 100

    @model_validator(mode="after")
    def check_at_capacity_intervals(self) -> _PollIntervalConfigModel:
        if not self._zero_or_ge_100(self.poll_interval_ms_at_capacity):
            raise ValueError("poll_interval_ms_at_capacity must be 0 or >= 100")
        if not self._zero_or_ge_100(self.multisession_poll_interval_ms_at_capacity):
            raise ValueError("multisession_poll_interval_ms_at_capacity must be 0 or >= 100")
        return self

    @model_validator(mode="after")
    def check_liveness(self) -> _PollIntervalConfigModel:
        if self.non_exclusive_heartbeat_interval_ms <= 0 and self.poll_interval_ms_at_capacity <= 0:
            raise ValueError(
                "at-capacity liveness requires non_exclusive_heartbeat_interval_ms > 0 "
                "or poll_interval_ms_at_capacity > 0"
            )
        if self.non_exclusive_heartbeat_interval_ms <= 0 and self.multisession_poll_interval_ms_at_capacity <= 0:
            raise ValueError(
                "at-capacity liveness requires non_exclusive_heartbeat_interval_ms > 0 "
                "or multisession_poll_interval_ms_at_capacity > 0"
            )
        return self

    def to_dataclass(self) -> PollIntervalConfig:
        return PollIntervalConfig(
            poll_interval_ms_not_at_capacity=self.poll_interval_ms_not_at_capacity,
            poll_interval_ms_at_capacity=self.poll_interval_ms_at_capacity,
            non_exclusive_heartbeat_interval_ms=self.non_exclusive_heartbeat_interval_ms,
            multisession_poll_interval_ms_not_at_capacity=self.multisession_poll_interval_ms_not_at_capacity,
            multisession_poll_interval_ms_partial_capacity=self.multisession_poll_interval_ms_partial_capacity,
            multisession_poll_interval_ms_at_capacity=self.multisession_poll_interval_ms_at_capacity,
            reclaim_older_than_ms=self.reclaim_older_than_ms,
            session_keepalive_interval_v2_ms=self.session_keepalive_interval_v2_ms,
        )


def get_poll_interval_config() -> PollIntervalConfig:
    """Fetch from GrowthBook with validation; fall back to defaults on failure."""
    # TODO: get_feature_value_cached_with_refresh('tengu_bridge_poll_interval_config', ...)
    raw: Any = asdict(DEFAULT_POLL_CONFIG)
    try:
        model = _PollIntervalConfigModel.model_validate(raw)
        return model.to_dataclass()
    except Exception:
        return DEFAULT_POLL_CONFIG
