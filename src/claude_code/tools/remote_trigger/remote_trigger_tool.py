"""Remote trigger API tool (httpx)."""

from __future__ import annotations

import json
from dataclasses import dataclass
from typing import Any, Literal

import httpx

from ...core.tool import Tool, ToolCallProgress, ToolResult, ToolUseContext
from .prompt import DESCRIPTION, PROMPT, REMOTE_TRIGGER_TOOL_NAME

TriggerAction = Literal["list", "get", "create", "update", "run"]

TRIGGERS_BETA = "ccr-triggers-2026-01-30"


@dataclass
class RemoteTriggerInput:
    action: TriggerAction
    trigger_id: str | None = None
    body: dict[str, Any] | None = None


@dataclass
class RemoteTriggerOutput:
    status: int
    json: str


INPUT_SCHEMA: dict[str, Any] = {
    "type": "object",
    "additionalProperties": False,
    "properties": {
        "action": {"type": "string", "enum": ["list", "get", "create", "update", "run"]},
        "trigger_id": {"type": "string", "pattern": r"^[\w-]+$"},
        "body": {"type": "object", "additionalProperties": True},
    },
    "required": ["action"],
}


class RemoteTriggerTool(Tool):
    name = REMOTE_TRIGGER_TOOL_NAME
    description = DESCRIPTION
    input_schema = INPUT_SCHEMA
    is_read_only = False
    is_concurrency_safe = True

    async def call(
        self,
        input_data: dict[str, Any],
        context: ToolUseContext,
        progress_callback: ToolCallProgress | None = None,
    ) -> ToolResult[RemoteTriggerOutput]:
        action = input_data["action"]
        trigger_id = input_data.get("trigger_id")
        body = input_data.get("body")

        token_provider = (context.options or {}).get("remote_trigger_token")
        org_provider = (context.options or {}).get("remote_trigger_org_uuid")
        base_url = (context.options or {}).get("remote_trigger_base_url", "https://api.anthropic.com")

        if not callable(token_provider):
            raise RuntimeError(
                "Set context.options['remote_trigger_token'] to an async callable returning a bearer token.",
            )
        token = await token_provider()
        if not token:
            raise RuntimeError("Not authenticated. Run /login and try again.")

        org_uuid = None
        if callable(org_provider):
            org_uuid = await org_provider()
        if not org_uuid:
            raise RuntimeError("Unable to resolve organization UUID.")

        base = f"{base_url.rstrip('/')}/v1/code/triggers"
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
                raise ValueError("get requires trigger_id")
            method, url = "GET", f"{base}/{trigger_id}"
        elif action == "create":
            if not body:
                raise ValueError("create requires body")
            method, url, json_body = "POST", base, body
        elif action == "update":
            if not trigger_id or not body:
                raise ValueError("update requires trigger_id and body")
            method, url, json_body = "POST", f"{base}/{trigger_id}", body
        elif action == "run":
            if not trigger_id:
                raise ValueError("run requires trigger_id")
            method, url, json_body = "POST", f"{base}/{trigger_id}/run", {}
        else:
            raise ValueError(f"Unknown action: {action}")

        async with httpx.AsyncClient(timeout=20.0) as client:
            resp = await client.request(
                method,
                url,
                headers=headers,
                json=json_body,
            )

        try:
            payload: Any = resp.json()
        except Exception:
            payload = {"raw": resp.text}

        return ToolResult(
            data=RemoteTriggerOutput(status=resp.status_code, json=json.dumps(payload)),
        )


def remote_trigger_documentation() -> str:
    return PROMPT
