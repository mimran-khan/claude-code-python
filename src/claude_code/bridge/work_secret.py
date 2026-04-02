"""Work secret decoding and SDK URL builders (ported from bridge/workSecret.ts)."""

from __future__ import annotations

import base64
import json
import re
from typing import Any, cast

import httpx

from claude_code.bridge.types import WorkSecret


def decode_work_secret(secret: str) -> WorkSecret:
    pad = 4 - len(secret) % 4
    if pad != 4:
        secret += "=" * pad
    raw = base64.urlsafe_b64decode(secret.encode("ascii"))
    text = raw.decode("utf-8")
    parsed: Any = json.loads(text)
    if not isinstance(parsed, dict) or parsed.get("version") != 1:
        ver = parsed.get("version") if isinstance(parsed, dict) else "unknown"
        raise ValueError(f"Unsupported work secret version: {ver}")
    obj = cast(dict[str, Any], parsed)
    if not obj.get("session_ingress_token") or not isinstance(obj["session_ingress_token"], str):
        raise ValueError("Invalid work secret: missing or empty session_ingress_token")
    if not isinstance(obj.get("api_base_url"), str):
        raise ValueError("Invalid work secret: missing api_base_url")
    sources = obj.get("sources") if isinstance(obj.get("sources"), list) else []
    auth = obj.get("auth") if isinstance(obj.get("auth"), list) else []
    return WorkSecret(
        version=1,
        session_ingress_token=obj["session_ingress_token"],
        api_base_url=obj["api_base_url"],
        sources=sources,
        auth=auth,
        claude_code_args=obj.get("claude_code_args"),
        mcp_config=obj.get("mcp_config"),
        environment_variables=obj.get("environment_variables"),
        use_code_sessions=obj.get("use_code_sessions"),
    )


def build_sdk_url(api_base_url: str, session_id: str) -> str:
    is_localhost = "localhost" in api_base_url or "127.0.0.1" in api_base_url
    protocol = "ws" if is_localhost else "wss"
    version = "v2" if is_localhost else "v1"
    host = re.sub(r"^https?://", "", api_base_url)
    host = host.rstrip("/")
    return f"{protocol}://{host}/{version}/session_ingress/ws/{session_id}"


def same_session_id(a: str, b: str) -> bool:
    if a == b:
        return True
    a_body = a[a.rfind("_") + 1 :]
    b_body = b[b.rfind("_") + 1 :]
    return len(a_body) >= 4 and a_body == b_body


def build_ccr_v2_sdk_url(api_base_url: str, session_id: str) -> str:
    base = api_base_url.rstrip("/")
    return f"{base}/v1/code/sessions/{session_id}"


async def register_worker(session_url: str, access_token: str) -> int:
    url = f"{session_url.rstrip('/')}/worker/register"
    async with httpx.AsyncClient() as client:
        response = await client.post(
            url,
            json={},
            headers={
                "Authorization": f"Bearer {access_token}",
                "Content-Type": "application/json",
                "anthropic-version": "2023-06-01",
            },
            timeout=10.0,
        )
    response.raise_for_status()
    data = response.json()
    raw = data.get("worker_epoch")
    epoch = int(raw) if isinstance(raw, str) else raw
    if not isinstance(epoch, int) or epoch < 0:
        raise ValueError(f"register_worker: invalid worker_epoch: {data!r}")
    return epoch
