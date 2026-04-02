"""Env-less bridge timing config (ported from bridge/envLessBridgeConfig.ts)."""

from __future__ import annotations

import os
import re
from typing import Any

from pydantic import BaseModel, Field, field_validator

from claude_code.bridge.bridge_enabled import is_env_less_bridge_enabled

# TODO: MACRO.VERSION from build metadata
_CLI_VERSION = os.environ.get("CLAUDE_CODE_VERSION", "0.0.0")


class EnvLessBridgeConfig(BaseModel):
    init_retry_max_attempts: int = Field(default=3, ge=1, le=10)
    init_retry_base_delay_ms: int = Field(default=500, ge=100)
    init_retry_jitter_fraction: float = Field(default=0.25, ge=0, le=1)
    init_retry_max_delay_ms: int = Field(default=4000, ge=500)
    http_timeout_ms: int = Field(default=10_000, ge=2000)
    uuid_dedup_buffer_size: int = Field(default=2000, ge=100, le=50_000)
    heartbeat_interval_ms: int = Field(default=20_000, ge=5000, le=30_000)
    heartbeat_jitter_fraction: float = Field(default=0.1, ge=0, le=0.5)
    token_refresh_buffer_ms: int = Field(default=300_000, ge=30_000, le=1_800_000)
    teardown_archive_timeout_ms: int = Field(default=1500, ge=500, le=2000)
    connect_timeout_ms: int = Field(default=15_000, ge=5000, le=60_000)
    min_version: str = Field(default="0.0.0")
    should_show_app_upgrade_message: bool = False

    @field_validator("min_version")
    @classmethod
    def semver_parseable(cls, v: str) -> str:
        if not v or not re.match(r"^[\d.]+", v):
            raise ValueError("min_version must be a semver-like string")
        return v


DEFAULT_ENV_LESS_BRIDGE_CONFIG = EnvLessBridgeConfig()


def _version_lt(a: str, b: str) -> bool:
    """Rough semver compare: a < b."""
    try:
        ap = [int(x) for x in re.split(r"[-+]", a)[0].split(".") if x.isdigit()]
        bp = [int(x) for x in re.split(r"[-+]", b)[0].split(".") if x.isdigit()]
        while len(ap) < 3:
            ap.append(0)
        while len(bp) < 3:
            bp.append(0)
        return tuple(ap[:3]) < tuple(bp[:3])
    except Exception:
        return False


async def get_env_less_bridge_config() -> EnvLessBridgeConfig:
    # TODO: await get_feature_value_deprecated('tengu_bridge_repl_v2_config', ...)
    raw: Any = DEFAULT_ENV_LESS_BRIDGE_CONFIG.model_dump()
    try:
        return EnvLessBridgeConfig.model_validate(raw)
    except Exception:
        return DEFAULT_ENV_LESS_BRIDGE_CONFIG


async def check_env_less_bridge_min_version() -> str | None:
    cfg = await get_env_less_bridge_config()
    if cfg.min_version and _version_lt(_CLI_VERSION, cfg.min_version):
        return (
            f"Your version of Claude Code ({_CLI_VERSION}) is too old for Remote Control.\n"
            f"Version {cfg.min_version} or higher is required. Run `claude update` to update."
        )
    return None


async def should_show_app_upgrade_message() -> bool:
    if not is_env_less_bridge_enabled():
        return False
    cfg = await get_env_less_bridge_config()
    return cfg.should_show_app_upgrade_message
