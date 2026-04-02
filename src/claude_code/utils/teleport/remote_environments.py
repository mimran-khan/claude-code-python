"""
Environment providers API (Sessions / CCR).

Migrated from: utils/teleport/environments.ts
"""

from __future__ import annotations

import logging
from dataclasses import dataclass
from typing import Any, Literal

import httpx

logger = logging.getLogger(__name__)

EnvironmentKind = Literal["anthropic_cloud", "byoc", "bridge"]
EnvironmentState = Literal["active"]


@dataclass
class EnvironmentResource:
    kind: EnvironmentKind
    environment_id: str
    name: str
    created_at: str
    state: EnvironmentState


def _headers(access_token: str, org_uuid: str) -> dict[str, str]:

    from .api import CCR_BYOC_BETA, get_oauth_headers

    h = dict(get_oauth_headers(access_token))
    h["Content-Type"] = "application/json"
    h["anthropic-version"] = "2023-06-01"
    h["anthropic-beta"] = CCR_BYOC_BETA
    h["x-organization-uuid"] = org_uuid
    return h


async def fetch_environments() -> list[EnvironmentResource]:
    from claude_code.constants.oauth import get_oauth_config

    from .api import prepare_api_request

    creds = await prepare_api_request()
    if not creds.access_token:
        raise RuntimeError(
            "Claude Code web sessions require OAuth; set CLAUDE_OAUTH_ACCESS_TOKEN or configure token storage."
        )
    if not creds.org_uuid:
        raise RuntimeError("Unable to get organization UUID (CLAUDE_ORG_UUID).")

    base = get_oauth_config().BASE_API_URL
    url = f"{base}/v1/environment_providers"
    headers = _headers(creds.access_token, creds.org_uuid)

    try:
        async with httpx.AsyncClient(timeout=15.0) as client:
            r = await client.get(url, headers=headers)
            r.raise_for_status()
            body = r.json()
    except Exception as e:
        logger.error("fetch_environments failed: %s", e)
        raise RuntimeError(f"Failed to fetch environments: {e}") from e

    envs = body.get("environments") or []
    out: list[EnvironmentResource] = []
    for row in envs:
        if not isinstance(row, dict):
            continue
        out.append(
            EnvironmentResource(
                kind=row.get("kind", "anthropic_cloud"),
                environment_id=str(row.get("environment_id", "")),
                name=str(row.get("name", "")),
                created_at=str(row.get("created_at", "")),
                state=row.get("state", "active"),
            )
        )
    return out


async def create_default_cloud_environment(name: str) -> EnvironmentResource:
    from claude_code.constants.oauth import get_oauth_config

    from .api import prepare_api_request

    creds = await prepare_api_request()
    if not creds.access_token or not creds.org_uuid:
        raise RuntimeError("No access token available")

    base = get_oauth_config().BASE_API_URL
    url = f"{base}/v1/environment_providers/cloud/create"
    payload: dict[str, Any] = {
        "name": name,
        "kind": "anthropic_cloud",
        "description": "",
        "config": {
            "environment_type": "anthropic",
            "cwd": "/home/user",
            "init_script": None,
            "environment": {},
            "languages": [
                {"name": "python", "version": "3.11"},
                {"name": "node", "version": "20"},
            ],
            "network_config": {"allowed_hosts": [], "allow_default_hosts": True},
        },
    }
    headers = _headers(creds.access_token, creds.org_uuid)
    async with httpx.AsyncClient(timeout=15.0) as client:
        r = await client.post(url, headers=headers, json=payload)
        r.raise_for_status()
        row = r.json()
    return EnvironmentResource(
        kind=row.get("kind", "anthropic_cloud"),
        environment_id=str(row.get("environment_id", "")),
        name=str(row.get("name", name)),
        created_at=str(row.get("created_at", "")),
        state=row.get("state", "active"),
    )
