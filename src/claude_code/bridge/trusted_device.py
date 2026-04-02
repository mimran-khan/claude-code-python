"""Trusted device token for bridge sessions (ported from bridge/trustedDevice.ts)."""

from __future__ import annotations

import logging
import os
import platform
import socket
from functools import lru_cache

import httpx

logger = logging.getLogger(__name__)
TRUSTED_DEVICE_GATE = "tengu_sessions_elevated_auth_enforcement"
TRUSTED_DEVICE_STORAGE_SERVICE = "claude-code-python"
TRUSTED_DEVICE_STORAGE_ACCOUNT = "trusted-device-token-v1"


def _gate_enabled() -> bool:
    if os.environ.get("CLAUDE_TRUSTED_DEVICE_GATE", "").lower() in ("1", "true", "yes"):
        return True
    return False


@lru_cache(maxsize=1)
def _read_stored_token_cached() -> str | None:
    env_tok = os.environ.get("CLAUDE_TRUSTED_DEVICE_TOKEN")
    if env_tok:
        return env_tok
    from ..utils.secure_storage import get_credential

    return get_credential(TRUSTED_DEVICE_STORAGE_SERVICE, TRUSTED_DEVICE_STORAGE_ACCOUNT)


def get_trusted_device_token() -> str | None:
    if not _gate_enabled():
        return None
    return _read_stored_token_cached()


def clear_trusted_device_token_cache() -> None:
    _read_stored_token_cached.cache_clear()


def clear_trusted_device_token() -> None:
    if not _gate_enabled():
        return
    from ..utils.secure_storage import delete_credential

    delete_credential(TRUSTED_DEVICE_STORAGE_SERVICE, TRUSTED_DEVICE_STORAGE_ACCOUNT)
    _read_stored_token_cached.cache_clear()


async def enroll_trusted_device() -> None:
    try:
        if not _gate_enabled():
            logger.debug("[trusted-device] Gate off, skipping enrollment")
            return
        if os.environ.get("CLAUDE_TRUSTED_DEVICE_TOKEN"):
            return
        from ..constants.oauth import get_oauth_config
        from ..services.oauth.client import get_claude_ai_oauth_tokens
        from ..utils.secure_storage import set_credential

        tokens = get_claude_ai_oauth_tokens()
        access_token = tokens.access_token if tokens else None
        if not access_token:
            return
        base_url = get_oauth_config().BASE_API_URL
        hostname = socket.gethostname()
        display = f"Claude Code on {hostname} · {platform.system()}"
        async with httpx.AsyncClient() as client:
            r = await client.post(
                f"{base_url.rstrip('/')}/api/auth/trusted_devices",
                json={"display_name": display},
                headers={
                    "Authorization": f"Bearer {access_token}",
                    "Content-Type": "application/json",
                },
                timeout=10.0,
            )
        if r.status_code not in (200, 201):
            logger.debug("[trusted-device] Enrollment failed %s", r.status_code)
            return
        payload = r.json() if r.content else {}
        device_token = None
        if isinstance(payload, dict):
            device_token = payload.get("token") or payload.get("device_token") or payload.get("trusted_device_token")
        if not device_token or not isinstance(device_token, str):
            logger.debug("[trusted-device] Enrollment response missing token")
            return
        set_credential(TRUSTED_DEVICE_STORAGE_SERVICE, TRUSTED_DEVICE_STORAGE_ACCOUNT, device_token)
        _read_stored_token_cached.cache_clear()
    except Exception as e:
        logger.debug("[trusted-device] Enrollment error: %s", e)
