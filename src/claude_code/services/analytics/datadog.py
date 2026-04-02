"""
Datadog HTTP logs intake for allowed CLI events.

Migrated from: services/analytics/datadog.ts
"""

from __future__ import annotations

import hashlib
import os
import re
import threading
from functools import lru_cache
from typing import Any

import httpx
import structlog

from ...model.cost import MODEL_COSTS
from ...utils.model.providers import get_api_provider
from .metadata import enrich_metadata, get_event_metadata
from .sink_killswitch import is_sink_killed

logger = structlog.get_logger(__name__)

DATADOG_LOGS_ENDPOINT = "https://http-intake.logs.us5.datadoghq.com/api/v2/logs"
DATADOG_CLIENT_TOKEN = "pubbbf48e6d78dae54bceaa4acf463299bf"
DEFAULT_FLUSH_INTERVAL_MS = 15_000
MAX_BATCH_SIZE = 100
NETWORK_TIMEOUT_MS = 5.0

DATADOG_ALLOWED_EVENTS: frozenset[str] = frozenset(
    [
        "chrome_bridge_connection_succeeded",
        "chrome_bridge_connection_failed",
        "chrome_bridge_disconnected",
        "chrome_bridge_tool_call_completed",
        "chrome_bridge_tool_call_error",
        "chrome_bridge_tool_call_started",
        "chrome_bridge_tool_call_timeout",
        "tengu_api_error",
        "tengu_api_success",
        "tengu_brief_mode_enabled",
        "tengu_brief_mode_toggled",
        "tengu_brief_send",
        "tengu_cancel",
        "tengu_compact_failed",
        "tengu_exit",
        "tengu_flicker",
        "tengu_init",
        "tengu_model_fallback_triggered",
        "tengu_oauth_error",
        "tengu_oauth_success",
        "tengu_oauth_token_refresh_failure",
        "tengu_oauth_token_refresh_success",
        "tengu_oauth_token_refresh_lock_acquiring",
        "tengu_oauth_token_refresh_lock_acquired",
        "tengu_oauth_token_refresh_starting",
        "tengu_oauth_token_refresh_completed",
        "tengu_oauth_token_refresh_lock_releasing",
        "tengu_oauth_token_refresh_lock_released",
        "tengu_query_error",
        "tengu_session_file_read",
        "tengu_started",
        "tengu_tool_use_error",
        "tengu_tool_use_granted_in_prompt_permanent",
        "tengu_tool_use_granted_in_prompt_temporary",
        "tengu_tool_use_rejected_in_prompt",
        "tengu_tool_use_success",
        "tengu_uncaught_exception",
        "tengu_unhandled_rejection",
        "tengu_voice_recording_started",
        "tengu_voice_toggled",
        "tengu_team_mem_sync_pull",
        "tengu_team_mem_sync_push",
        "tengu_team_mem_sync_started",
        "tengu_team_mem_entries_capped",
    ]
)

TAG_FIELDS = (
    "arch",
    "clientType",
    "errorType",
    "http_status_range",
    "http_status",
    "kairosActive",
    "model",
    "platform",
    "provider",
    "skillMode",
    "subscriptionType",
    "toolName",
    "userBucket",
    "userType",
    "version",
    "versionBase",
)

_log_batch: list[dict[str, Any]] = []
_flush_timer: threading.Timer | None = None
_datadog_initialized: bool | None = None
_batch_lock = threading.Lock()


def _camel_to_snake(name: str) -> str:
    return re.sub(r"([A-Z])", r"_\1", name).lower().lstrip("_")


def _get_flush_interval_ms() -> int:
    raw = os.environ.get("CLAUDE_CODE_DATADOG_FLUSH_INTERVAL_MS", "")
    if raw.isdigit():
        return int(raw)
    return DEFAULT_FLUSH_INTERVAL_MS


def _flush_logs() -> None:
    global _log_batch
    to_send: list[dict[str, Any]]
    with _batch_lock:
        if not _log_batch:
            return
        to_send = _log_batch
        _log_batch = []
    try:
        with httpx.Client(timeout=NETWORK_TIMEOUT_MS) as client:
            client.post(
                DATADOG_LOGS_ENDPOINT,
                json=to_send,
                headers={
                    "Content-Type": "application/json",
                    "DD-API-KEY": DATADOG_CLIENT_TOKEN,
                },
            )
    except Exception as e:
        logger.warning("datadog_flush_failed", error=str(e))


def _schedule_flush() -> None:
    global _flush_timer
    if _flush_timer is not None:
        return

    def _run() -> None:
        global _flush_timer
        _flush_timer = None
        _flush_logs()

    _flush_timer = threading.Timer(_get_flush_interval_ms() / 1000.0, _run)
    _flush_timer.daemon = True
    _flush_timer.start()


@lru_cache(maxsize=1)
def initialize_datadog() -> bool:
    from .config import is_analytics_disabled

    global _datadog_initialized
    if is_analytics_disabled():
        _datadog_initialized = False
        return False
    _datadog_initialized = True
    return True


def shutdown_datadog() -> None:
    global _flush_timer
    if _flush_timer is not None:
        _flush_timer.cancel()
        _flush_timer = None
    _flush_logs()


def _get_user_bucket() -> int:
    import uuid

    user_id = os.environ.get("CLAUDE_USER_ID") or str(uuid.uuid4())
    digest = hashlib.sha256(user_id.encode()).hexdigest()
    return int(digest[:8], 16) % 30


def track_datadog_event(
    event_name: str,
    properties: dict[str, bool | int | float | str | None],
) -> None:
    if os.environ.get("NODE_ENV") != "production":
        return
    if get_api_provider() != "firstParty":
        return
    if is_sink_killed("datadog"):
        return

    global _datadog_initialized
    initialized = _datadog_initialized
    if initialized is None:
        initialized = initialize_datadog()
    if not initialized or event_name not in DATADOG_ALLOWED_EVENTS:
        return

    global _log_batch, _flush_timer

    try:
        base = dict(get_event_metadata())
        metadata = enrich_metadata(base, dict(properties))
        env_context = metadata.pop("envContext", {}) if isinstance(metadata, dict) else {}
        if not isinstance(env_context, dict):
            env_context = {}
        all_data: dict[str, Any] = {**metadata, **env_context, **dict(properties)}
        all_data["userBucket"] = _get_user_bucket()

        tool_name = all_data.get("toolName")
        if isinstance(tool_name, str) and tool_name.startswith("mcp__"):
            all_data["toolName"] = "mcp"

        model_val = all_data.get("model")
        if os.environ.get("USER_TYPE") != "ant" and isinstance(model_val, str):
            cleaned = re.sub(r"\[1m]$", "", model_val, flags=re.I)
            all_data["model"] = cleaned if cleaned in MODEL_COSTS else "other"

        version_val = all_data.get("version")
        if isinstance(version_val, str):
            all_data["version"] = re.sub(
                r"^(\d+\.\d+\.\d+-dev\.\d{8})\.t\d+\.sha[a-f0-9]+$",
                r"\1",
                version_val,
            )

        status = all_data.pop("status", None)
        if status is not None:
            status_code = str(status)
            all_data["http_status"] = status_code
            first = status_code[:1]
            if first in "12345":
                all_data["http_status_range"] = f"{first}xx"

        tags = [f"event:{event_name}"]
        for field in TAG_FIELDS:
            v = all_data.get(field)
            if v is not None:
                tags.append(f"{_camel_to_snake(str(field))}:{v}")

        log_entry: dict[str, Any] = {
            "ddsource": "nodejs",
            "ddtags": ",".join(tags),
            "message": event_name,
            "service": "claude-code",
            "hostname": "claude-code",
            "env": os.environ.get("USER_TYPE"),
        }
        for key, value in all_data.items():
            if value is not None:
                log_entry[_camel_to_snake(key)] = value

        to_send: list[dict[str, Any]] = []
        with _batch_lock:
            _log_batch.append(log_entry)
            if len(_log_batch) >= MAX_BATCH_SIZE:
                if _flush_timer is not None:
                    _flush_timer.cancel()
                    _flush_timer = None
                to_send = _log_batch
                _log_batch = []
        if to_send:
            try:
                with httpx.Client(timeout=NETWORK_TIMEOUT_MS) as client:
                    client.post(
                        DATADOG_LOGS_ENDPOINT,
                        json=to_send,
                        headers={
                            "Content-Type": "application/json",
                            "DD-API-KEY": DATADOG_CLIENT_TOKEN,
                        },
                    )
            except Exception as e:
                logger.warning("datadog_immediate_flush_failed", error=str(e))
        else:
            _schedule_flush()
    except Exception as e:
        logger.warning("track_datadog_event_failed", error=str(e))
