"""Bundled /schedule remote agents skill. Migrated from: skills/bundled/scheduleRemoteAgents.ts"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from zoneinfo import ZoneInfo

from ...constants.tools import ASK_USER_QUESTION_TOOL_NAME
from ...services.oauth.client import get_claude_ai_oauth_tokens
from ...tools.remote_trigger.prompt import REMOTE_TRIGGER_TOOL_NAME
from ...utils.debug import log_for_debugging
from ...utils.detect_repository import detect_current_repository_with_host
from ...utils.git import get_remote_url
from ...utils.teleport.remote_environments import (
    create_default_cloud_environment,
    fetch_environments,
)
from ..bundled_registry import register_bundled_skill
from ..types import BundledSkillDefinition, ToolUseContext

BASE58 = "123456789ABCDEFGHJKLMNPQRSTUVWXYZabcdefghijkmnopqrstuvwxyz"


def _tagged_id_to_uuid(tagged_id: str) -> str | None:
    prefix = "mcpsrv_"
    if not tagged_id.startswith(prefix):
        return None
    rest = tagged_id[len(prefix) :]
    base58_data = rest[2:]
    n = 0
    for c in base58_data:
        idx = BASE58.find(c)
        if idx < 0:
            return None
        n = n * 58 + idx
    hex_str = format(n, "x").zfill(32)
    return f"{hex_str[:8]}-{hex_str[8:12]}-{hex_str[12:16]}-{hex_str[16:20]}-{hex_str[20:32]}"


@dataclass
class ConnectorInfo:
    uuid: str
    name: str
    url: str


def _sanitize_connector_name(name: str) -> str:
    import re

    s = re.sub(r"^claude[.\s-]ai[.\s-]", "", name, flags=re.I)
    s = re.sub(r"[^a-zA-Z0-9_-]", "-", s)
    s = re.sub(r"-+", "-", s).strip("-")
    return s


def _get_connected_claude_ai_connectors(mcp_clients: list[object]) -> list[ConnectorInfo]:
    out: list[ConnectorInfo] = []
    for client in mcp_clients:
        ctype = getattr(client, "type", None)
        if ctype != "connected":
            continue
        cfg = getattr(client, "config", None)
        if cfg is None or getattr(cfg, "type", None) != "claudeai-proxy":
            continue
        cid = getattr(cfg, "id", None)
        url = getattr(cfg, "url", "") or ""
        if not isinstance(cid, str):
            continue
        uuid = _tagged_id_to_uuid(cid)
        if not uuid:
            continue
        name = getattr(client, "name", "connector") or "connector"
        out.append(ConnectorInfo(uuid=uuid, name=str(name), url=str(url)))
    return out


def _format_connectors(connectors: list[ConnectorInfo]) -> str:
    if not connectors:
        return "No connected MCP connectors found. Connect at https://claude.ai/settings/connectors"
    lines = ["Connected connectors (available for triggers):"]
    for c in connectors:
        safe = _sanitize_connector_name(c.name)
        lines.append(f"- {c.name} (connector_uuid: {c.uuid}, name: {safe}, url: {c.url})")
    return "\n".join(lines)


async def _git_repo_https_url() -> str | None:
    remote_url = await get_remote_url()
    if not remote_url:
        return None
    try:
        from ...utils.detect_repository import parse_git_remote

        parsed = parse_git_remote(remote_url)
    except Exception:
        return None
    if not parsed:
        return None
    return f"https://{parsed.host}/{parsed.owner}/{parsed.name}"


def _build_schedule_prompt(
    *,
    user_timezone: str,
    connectors_info: str,
    git_repo_url: str | None,
    environments_info: str,
    created_note: str,
    setup_notes: str,
    user_args: str,
) -> str:
    first_step = (
        "The user already provided a request at the bottom — skip the initial menu."
        if user_args.strip()
        else f"First use {ASK_USER_QUESTION_TOOL_NAME} with options: create / list / update / run."
    )
    repo_hint = (
        f" Default git repo: `{git_repo_url}`."
        if git_repo_url
        else " Ask which git repositories the remote agent needs."
    )
    return f"""# Schedule Remote Agents

Use `{REMOTE_TRIGGER_TOOL_NAME}` (load via ToolSearch if needed) for list/get/create/update/run.

## First step
{first_step}

## Connectors
{connectors_info}

## Environments
{environments_info}
{created_note}

## Timezone
User timezone: **{user_timezone}**. Cron expressions are in UTC — convert and confirm.

## Git
{repo_hint}

## Setup notes
{setup_notes}

## User request
{user_args if user_args.strip() else "(none — use AskUserQuestion to clarify)"}

After create, share `https://claude.ai/code/scheduled/{{trigger_id}}` when you have an id.
"""


def _schedule_skill_enabled() -> bool:
    import os

    return os.environ.get("CLAUDE_CODE_REMOTE_SCHEDULE", "").lower() in ("1", "true", "yes")


def register_schedule_remote_agents_skill() -> None:
    async def get_prompt_for_command(args: str, ctx: ToolUseContext) -> list[dict[str, str]]:
        tokens = get_claude_ai_oauth_tokens()
        if not tokens or not getattr(tokens, "access_token", None):
            return [
                {
                    "type": "text",
                    "text": (
                        "Authenticate with a claude.ai account first (not API-key only). "
                        "Run /login, then try /schedule again."
                    ),
                },
            ]

        try:
            environments = await fetch_environments()
        except Exception as err:
            log_for_debugging(f"[schedule] fetch environments: {err}", level="warn")
            return [
                {
                    "type": "text",
                    "text": "Could not load remote environments. Try again shortly or check OAuth.",
                },
            ]

        created_note = ""
        if not environments:
            try:
                env = await create_default_cloud_environment("claude-code-default")
                environments = [env]
                created_note = f"\n**Note:** Created default environment `{env.name}` (id `{env.environment_id}`).\n"
            except Exception as err:
                log_for_debugging(f"[schedule] create env: {err}", level="warn")
                return [
                    {
                        "type": "text",
                        "text": (
                            "No remote environments and could not create one. "
                            "Visit https://claude.ai/code to configure, then retry."
                        ),
                    },
                ]

        setup_notes_list: list[str] = []
        repo = await detect_current_repository_with_host()
        if repo is None:
            setup_notes_list.append("Not in a git repo — specify repository URLs explicitly in the trigger.")
        mcp_clients = getattr(getattr(ctx, "options", object()), "mcp_clients", []) or []
        connectors = _get_connected_claude_ai_connectors(list(mcp_clients))
        if not connectors:
            setup_notes_list.append(
                "No MCP connectors — connect at https://claude.ai/settings/connectors if needed.",
            )

        try:
            user_timezone = str(datetime.now(tz=ZoneInfo("UTC")).astimezone().tzinfo)
        except Exception:
            user_timezone = "UTC"

        env_lines = ["Available environments:"]
        for env in environments:
            env_lines.append(f"- {env.name} (id: {env.environment_id}, kind: {env.kind})")
        environments_info = "\n".join(env_lines)

        prompt = _build_schedule_prompt(
            user_timezone=user_timezone,
            connectors_info=_format_connectors(connectors),
            git_repo_url=await _git_repo_https_url(),
            environments_info=environments_info,
            created_note=created_note,
            setup_notes="\n".join(f"- {n}" for n in setup_notes_list) or "(none)",
            user_args=args,
        )
        return [{"type": "text", "text": prompt}]

    register_bundled_skill(
        BundledSkillDefinition(
            name="schedule",
            description="Create, update, list, or run scheduled remote Claude Code agents (cron triggers).",
            when_to_use="When the user wants recurring remote agents or cron-style automation on claude.ai.",
            user_invocable=True,
            is_enabled=_schedule_skill_enabled,
            allowed_tools=[REMOTE_TRIGGER_TOOL_NAME, ASK_USER_QUESTION_TOOL_NAME],
            get_prompt_for_command=get_prompt_for_command,
        ),
    )
