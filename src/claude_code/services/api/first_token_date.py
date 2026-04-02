"""Fetch and cache Claude Code first token date."""

from __future__ import annotations

from datetime import datetime

import httpx

from ...constants.oauth import get_oauth_config
from ...utils.http import get_auth_headers, get_user_agent


async def fetch_and_store_claude_code_first_token_date() -> None:
    """
    GET /api/organization/claude_code_first_token_date and persist to global config.

    Migrated from: services/api/firstTokenDate.ts
    """
    import json
    import os

    from ...utils.config_utils import get_global_config_path, save_global_config

    path = get_global_config_path()
    current: dict = {}
    if os.path.exists(path):
        try:
            with open(path, encoding="utf-8") as f:
                current = json.load(f)
        except (OSError, json.JSONDecodeError):
            current = {}
    if current.get("claudeCodeFirstTokenDate") is not None:
        return
    auth = get_auth_headers()
    if auth.error:
        return
    url = f"{get_oauth_config().BASE_API_URL}/api/organization/claude_code_first_token_date"
    async with httpx.AsyncClient(timeout=10.0) as client:
        r = await client.get(
            url,
            headers={**auth.headers, "User-Agent": get_user_agent()},
        )
        r.raise_for_status()
        body = r.json()
    first_token_date = body.get("first_token_date") if isinstance(body, dict) else None
    if first_token_date is not None:
        try:
            datetime.fromisoformat(str(first_token_date).replace("Z", "+00:00"))
        except ValueError:
            return

    def updater(prev: dict) -> dict:
        n = dict(prev)
        n["claudeCodeFirstTokenDate"] = first_token_date
        return n

    save_global_config(updater)
