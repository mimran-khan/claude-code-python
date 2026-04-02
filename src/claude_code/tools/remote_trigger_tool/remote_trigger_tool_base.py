"""
Remote trigger tool (async base.Tool).

Migrated from: tools/RemoteTriggerTool/RemoteTriggerTool.ts
"""

from __future__ import annotations

import json
from collections.abc import Awaitable, Callable
from dataclasses import dataclass
from typing import Any, Literal

import httpx

from ..base import Tool, ToolResult, ToolUseContext
from .prompt_text import DESCRIPTION, PROMPT, REMOTE_TRIGGER_TOOL_NAME

TriggerAction = Literal["list", "get", "create", "update", "run"]
TRIGGERS_BETA = "ccr-triggers-2026-01-30"

TokenProvider = Callable[[], Awaitable[str | None]]
OrgProvider = Callable[[], Awaitable[str | None]]


@dataclass
class RemoteTriggerOutput:
    """API response envelope matching TS output schema."""

    status: int
    json: str


class RemoteTriggerBaseTool(Tool[dict[str, Any], dict[str, Any]]):
    """Manage scheduled remote agent triggers via claude.ai CCR API."""

    def __init__(
        self,
        *,
        token_provider: TokenProvider | None = None,
        org_uuid_provider: OrgProvider | None = None,
        base_api_url: str = "https://api.anthropic.com",
    ) -> None:
        self._token_provider = token_provider
        self._org_uuid_provider = org_uuid_provider
        self._base_api_url = base_api_url.rstrip("/")

    @property
    def name(self) -> str:
        return REMOTE_TRIGGER_TOOL_NAME

    @property
    def search_hint(self) -> str | None:
        return "manage scheduled remote agent triggers"

    async def description(self) -> str:
        return DESCRIPTION

    async def prompt(self) -> str:
        return PROMPT

    def get_input_schema(self) -> dict[str, Any]:
        return {
            "type": "object",
            "additionalProperties": False,
            "properties": {
                "action": {
                    "type": "string",
                    "enum": ["list", "get", "create", "update", "run"],
                },
                "trigger_id": {"type": "string", "pattern": r"^[\w-]+$"},
                "body": {"type": "object", "additionalProperties": True},
            },
            "required": ["action"],
        }

    def get_output_schema(self) -> dict[str, Any]:
        return {
            "type": "object",
            "properties": {
                "status": {"type": "integer"},
                "json": {"type": "string"},
            },
            "required": ["status", "json"],
        }

    def _resolve_providers(
        self,
        context: ToolUseContext,
    ) -> tuple[TokenProvider, OrgProvider, str]:
        opts: dict[str, Any] = dict(context.read_file_state.get("remote_trigger_options") or {})
        if context.get_app_state:
            app = context.get_app_state()
            if isinstance(app, dict):
                extra = app.get("remote_trigger_options")
                if isinstance(extra, dict):
                    opts = {**opts, **extra}
            elif hasattr(app, "remote_trigger_options"):
                ro = getattr(app, "remote_trigger_options", None)
                if isinstance(ro, dict):
                    opts = {**opts, **ro}

        token_p = self._token_provider or opts.get("remote_trigger_token")
        org_p = self._org_uuid_provider or opts.get("remote_trigger_org_uuid")
        base = self._base_api_url
        bu = opts.get("remote_trigger_base_url")
        if isinstance(bu, str) and bu.strip():
            base = bu.rstrip("/")

        if not callable(token_p) or not callable(org_p):
            raise RuntimeError(
                "RemoteTriggerBaseTool requires async callables token_provider and "
                "org_uuid_provider via constructor or context remote_trigger_options.",
            )
        return token_p, org_p, base

    async def execute(
        self,
        input: dict[str, Any],
        context: ToolUseContext,
    ) -> ToolResult:
        action: TriggerAction = input["action"]  # type: ignore[assignment]
        trigger_id: str | None = input.get("trigger_id")
        body: dict[str, Any] | None = input.get("body")

        try:
            token_p, org_p, base_url = self._resolve_providers(context)
        except RuntimeError as e:
            return ToolResult(success=False, error=str(e))

        token = await token_p()
        if not token:
            return ToolResult(
                success=False,
                error="Not authenticated. Run /login and try again.",
            )
        org_uuid = await org_p()
        if not org_uuid:
            return ToolResult(success=False, error="Unable to resolve organization UUID.")

        base = f"{base_url}/v1/code/triggers"
        headers = {
            "Authorization": f"Bearer {token}",
            "Content-Type": "application/json",
            "anthropic-version": "2023-06-01",
            "anthropic-beta": TRIGGERS_BETA,
            "x-organization-uuid": org_uuid,
        }

        method = "GET"
        url = base
        json_body: Any = None

        if action == "list":
            method, url = "GET", base
        elif action == "get":
            if not trigger_id:
                return ToolResult(success=False, error="get requires trigger_id")
            method, url = "GET", f"{base}/{trigger_id}"
        elif action == "create":
            if not body:
                return ToolResult(success=False, error="create requires body")
            method, url, json_body = "POST", base, body
        elif action == "update":
            if not trigger_id or not body:
                return ToolResult(success=False, error="update requires trigger_id and body")
            method, url, json_body = "POST", f"{base}/{trigger_id}", body
        elif action == "run":
            if not trigger_id:
                return ToolResult(success=False, error="run requires trigger_id")
            method, url, json_body = "POST", f"{base}/{trigger_id}/run", {}
        else:
            return ToolResult(success=False, error=f"Unknown action: {action}")

        try:
            async with httpx.AsyncClient(timeout=20.0) as client:
                resp = await client.request(method, url, headers=headers, json=json_body)
        except httpx.HTTPError as e:
            return ToolResult(success=False, error=str(e))

        try:
            payload: Any = resp.json()
        except Exception:
            payload = {"raw": resp.text}

        out = RemoteTriggerOutput(status=resp.status_code, json=json.dumps(payload))
        return ToolResult(
            success=200 <= resp.status_code < 300,
            output={"status": out.status, "json": out.json},
        )
