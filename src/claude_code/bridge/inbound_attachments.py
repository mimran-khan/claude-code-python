"""Resolve file_uuid attachments on bridge messages (ported from bridge/inboundAttachments.ts)."""

from __future__ import annotations

import logging
import re
import uuid
from pathlib import Path
from typing import Any
from urllib.parse import quote

import httpx
from pydantic import BaseModel, Field

from claude_code.bridge.bridge_config import get_bridge_access_token, get_bridge_base_url

logger = logging.getLogger(__name__)
DOWNLOAD_TIMEOUT_MS = 30_000


class InboundAttachment(BaseModel):
    file_uuid: str
    file_name: str = Field(min_length=1)


def extract_inbound_attachments(msg: object) -> list[InboundAttachment]:
    if not isinstance(msg, dict) or "file_attachments" not in msg:
        return []
    raw = msg["file_attachments"]
    if not isinstance(raw, list):
        return []
    out: list[InboundAttachment] = []
    for item in raw:
        if not isinstance(item, dict):
            continue
        try:
            out.append(InboundAttachment.model_validate(item))
        except Exception:
            continue
    return out


def _sanitize_file_name(name: str) -> str:
    base = Path(name).name
    base = re.sub(r"[^a-zA-Z0-9._-]", "_", base)
    return base or "attachment"


def _uploads_dir(session_id: str) -> Path:
    home = Path.home()
    return home / ".claude" / "uploads" / session_id


async def resolve_inbound_attachments(
    attachments: list[InboundAttachment],
    session_id: str,
) -> str:
    if not attachments:
        return ""
    token = get_bridge_access_token()
    if not token:
        return ""
    try:
        base_url = get_bridge_base_url()
    except Exception:
        return ""
    paths: list[str] = []
    for att in attachments:
        url = f"{base_url.rstrip('/')}/api/oauth/files/{quote(att.file_uuid, safe='')}/content"
        try:
            async with httpx.AsyncClient() as client:
                r = await client.get(
                    url,
                    headers={"Authorization": f"Bearer {token}"},
                    timeout=DOWNLOAD_TIMEOUT_MS / 1000.0,
                )
            if r.status_code != 200:
                continue
            data = r.content
        except Exception:
            continue
        safe = _sanitize_file_name(att.file_name)
        prefix = (att.file_uuid[:8] or str(uuid.uuid4())[:8]).replace("/", "_")
        d = _uploads_dir(session_id)
        d.mkdir(parents=True, exist_ok=True)
        out_path = d / f"{prefix}-{safe}"
        out_path.write_bytes(data)
        paths.append(str(out_path))
    if not paths:
        return ""
    return " ".join(f'@"{p}"' for p in paths) + " "


def prepend_path_refs(
    content: str | list[dict[str, Any]],
    prefix: str,
) -> str | list[dict[str, Any]]:
    if not prefix:
        return content
    if isinstance(content, str):
        return prefix + content
    blocks = list(content)
    for i in range(len(blocks) - 1, -1, -1):
        b = blocks[i]
        if isinstance(b, dict) and b.get("type") == "text":
            nb = dict(b)
            nb["text"] = prefix + str(b.get("text", ""))
            blocks[i] = nb
            return blocks
    return [*blocks, {"type": "text", "text": prefix.rstrip()}]


async def resolve_and_prepend(
    msg: object,
    content: str | list[dict[str, Any]],
    session_id: str,
) -> str | list[dict[str, Any]]:
    atts = extract_inbound_attachments(msg)
    if not atts:
        return content
    prefix = await resolve_inbound_attachments(atts, session_id)
    return prepend_path_refs(content, prefix)
