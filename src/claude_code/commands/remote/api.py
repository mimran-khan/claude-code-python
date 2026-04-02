"""
Migrated from: commands/remote-setup/api.ts

HTTP helpers for CCR web onboarding (GitHub token import, default environment).
"""

from __future__ import annotations

import json
import logging
from dataclasses import dataclass
from typing import Any, Literal

logger = logging.getLogger(__name__)


class RedactedGithubToken:
    """Wraps a raw GitHub token so logs and str() never leak the value."""

    __slots__ = ("_value",)

    def __init__(self, raw: str) -> None:
        self._value = raw

    def reveal(self) -> str:
        return self._value

    def __str__(self) -> str:
        return "[REDACTED:gh-token]"

    def __repr__(self) -> str:
        return "[REDACTED:gh-token]"


@dataclass(frozen=True)
class ImportTokenResult:
    github_username: str


ImportTokenError = (
    Literal["not_signed_in"] | Literal["invalid_token"] | tuple[Literal["server"], int] | Literal["network"]
)


@dataclass(frozen=True)
class ImportGithubTokenOk:
    ok: Literal[True] = True
    result: ImportTokenResult | None = None


@dataclass(frozen=True)
class ImportGithubTokenErr:
    ok: Literal[False] = False
    error: ImportTokenError | None = None


async def import_github_token(
    token: RedactedGithubToken,
    *,
    base_api_url: str,
    access_token: str,
    org_uuid: str,
    post_json: Any | None = None,
) -> ImportGithubTokenOk | ImportGithubTokenErr:
    """
    POST GitHub token to CCR backend. Supply `post_json` as injected client
    (e.g. httpx) in production; when None, returns not_signed_in.
    """
    if post_json is None:
        return ImportGithubTokenErr(error="not_signed_in")

    url = f"{base_api_url.rstrip('/')}/v1/code/github/import-token"
    headers = {
        "Authorization": f"Bearer {access_token}",
        "anthropic-beta": "ccr-byoc-2025-07-29",
        "x-organization-uuid": org_uuid,
        "Content-Type": "application/json",
    }
    try:
        response = await post_json(
            url,
            headers=headers,
            json={"token": token.reveal()},
            timeout=15.0,
        )
        status = getattr(response, "status_code", 0)
        if status == 200:
            data = getattr(response, "json", lambda: {})()
            if callable(data):
                data = data()
            username = data.get("github_username", "")
            return ImportGithubTokenOk(
                result=ImportTokenResult(github_username=username),
            )
        if status == 400:
            return ImportGithubTokenErr(error="invalid_token")
        if status == 401:
            return ImportGithubTokenErr(error="not_signed_in")
        logger.error("import-token returned %s", status)
        return ImportGithubTokenErr(error=("server", status))
    except OSError:
        logger.exception("import-token network error")
        return ImportGithubTokenErr(error="network")


async def create_default_environment(
    *,
    base_api_url: str,
    access_token: str,
    org_uuid: str,
    fetch_environments: Any | None = None,
    post_json: Any | None = None,
) -> bool:
    """Best-effort default cloud environment creation (parity with TS)."""
    if fetch_environments is not None:
        try:
            envs = await fetch_environments()
            if len(envs) > 0:
                return True
        except Exception:
            pass

    if post_json is None:
        return False

    url = f"{base_api_url.rstrip('/')}/v1/environment_providers/cloud/create"
    headers = {
        "Authorization": f"Bearer {access_token}",
        "x-organization-uuid": org_uuid,
        "Content-Type": "application/json",
    }
    body = {
        "name": "Default",
        "kind": "anthropic_cloud",
        "description": "Default - trusted network access",
        "config": {
            "environment_type": "anthropic",
            "cwd": "/home/user",
            "init_script": None,
            "environment": {},
            "languages": [
                {"name": "python", "version": "3.11"},
                {"name": "node", "version": "20"},
            ],
            "network_config": {
                "allowed_hosts": [],
                "allow_default_hosts": True,
            },
        },
    }
    try:
        response = await post_json(
            url,
            headers=headers,
            content=json.dumps(body).encode(),
            timeout=15.0,
        )
        status = getattr(response, "status_code", 0)
        return 200 <= status < 300
    except OSError:
        return False


def get_code_web_url(claude_ai_origin: str) -> str:
    return f"{claude_ai_origin.rstrip('/')}/code"
