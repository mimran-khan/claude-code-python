"""
API bootstrap functions.

Initial API setup and configuration.

Migrated from: services/api/bootstrap.ts
"""

from __future__ import annotations

import logging
import os
from dataclasses import dataclass, field
from typing import Any

import httpx

from ...constants.oauth import CLAUDE_AI_PROFILE_SCOPE, OAUTH_BETA_HEADER, get_oauth_config
from ...utils.auth import get_anthropic_api_key
from ...utils.config_utils import load_global_config_dict, save_global_config
from ...utils.env_utils import is_env_truthy
from ...utils.http import get_user_agent
from ...utils.model.providers import get_api_provider
from ..oauth.client import get_claude_ai_oauth_tokens

logger = logging.getLogger(__name__)


@dataclass
class ModelOption:
    """An additional model option (maps API model/name/description)."""

    value: str
    label: str
    description: str


@dataclass
class BootstrapResponse:
    """Validated bootstrap API response."""

    client_data: dict[str, Any] | None = None
    additional_model_options: list[ModelOption] = field(default_factory=list)


def _parse_bootstrap_response(data: Any) -> BootstrapResponse | None:
    """Zod-equivalent validation for bootstrap JSON."""
    if not isinstance(data, dict):
        return None
    client_raw = data.get("client_data")
    client_data: dict[str, Any] | None
    if client_raw is None:
        client_data = None
    elif isinstance(client_raw, dict):
        client_data = client_raw
    else:
        return None

    raw_opts = data.get("additional_model_options")
    opts: list[ModelOption] = []
    if raw_opts is None:
        pass
    elif isinstance(raw_opts, list):
        for opt in raw_opts:
            if not isinstance(opt, dict):
                continue
            model = opt.get("model")
            name = opt.get("name")
            description = opt.get("description")
            if not isinstance(model, str) or not isinstance(name, str):
                continue
            desc = description if isinstance(description, str) else ""
            opts.append(ModelOption(value=model, label=name, description=desc))
    else:
        return None

    return BootstrapResponse(client_data=client_data, additional_model_options=opts)


async def fetch_bootstrap_api() -> BootstrapResponse | None:
    """
    GET /api/claude_cli/bootstrap (OAuth with profile scope preferred, else API key).
    """
    if is_env_truthy(os.getenv("CLAUDE_CODE_ESSENTIAL_TRAFFIC_ONLY", "")):
        return None

    if get_api_provider() != "firstParty":
        return None

    api_key = get_anthropic_api_key()
    tokens = get_claude_ai_oauth_tokens()
    scopes = list(tokens.scopes) if tokens else []
    has_oauth = bool(tokens and tokens.access_token and CLAUDE_AI_PROFILE_SCOPE in scopes)
    if not has_oauth and not api_key:
        return None

    cfg = get_oauth_config()
    url = f"{cfg.BASE_API_URL}/api/claude_cli/bootstrap"

    headers: dict[str, str] = {
        "Content-Type": "application/json",
        "User-Agent": get_user_agent(),
    }
    if has_oauth and tokens:
        headers["Authorization"] = f"Bearer {tokens.access_token}"
        headers["anthropic-beta"] = OAUTH_BETA_HEADER
    elif api_key:
        headers["x-api-key"] = api_key
    else:
        return None

    try:
        async with httpx.AsyncClient(timeout=5.0) as client:
            response = await client.get(url, headers=headers)
            if response.status_code != 200:
                return None
            return _parse_bootstrap_response(response.json())
    except Exception as exc:
        logger.debug("fetch_bootstrap_api failed: %s", exc)
        return None


async def fetch_bootstrap_data() -> None:
    """
    Fetch bootstrap and persist clientDataCache + additionalModelOptionsCache
    when changed (mirrors TS fetchBootstrapData).
    """
    try:
        response = await fetch_bootstrap_api()
        if response is None:
            return

        client_data = response.client_data
        additional_model_options = [
            {"value": o.value, "label": o.label, "description": o.description}
            for o in response.additional_model_options
        ]

        current = load_global_config_dict()
        if (
            current.get("clientDataCache") == client_data
            and current.get("additionalModelOptionsCache") == additional_model_options
        ):
            return

        def updater(c: dict[str, Any]) -> dict[str, Any]:
            n = dict(c)
            n["clientDataCache"] = client_data
            n["additionalModelOptionsCache"] = additional_model_options
            return n

        save_global_config(updater)
    except Exception as exc:
        logger.warning("fetch_bootstrap_data failed: %s", exc)


async def get_additional_models() -> list[ModelOption]:
    """Return additional model options from bootstrap API."""
    response = await fetch_bootstrap_api()
    if response:
        return response.additional_model_options
    return []
