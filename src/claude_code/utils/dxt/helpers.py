"""
DXT manifest parsing (MCPB JSON).

Migrated from: utils/dxt/helpers.ts
"""

from __future__ import annotations

import json
import re
from typing import Any

from pydantic import BaseModel, ConfigDict, Field, ValidationError

from ..errors import error_message


class McpbAuthor(BaseModel):
    model_config = ConfigDict(extra="allow")

    name: str = ""


class McpbManifest(BaseModel):
    model_config = ConfigDict(extra="allow")

    name: str = ""
    author: McpbAuthor = Field(default_factory=McpbAuthor)


async def validate_manifest(manifest_json: Any) -> McpbManifest:
    try:
        return McpbManifest.model_validate(manifest_json)
    except ValidationError as e:
        raise ValueError(f"Invalid manifest: {e}") from e


async def parse_and_validate_manifest_from_text(manifest_text: str) -> McpbManifest:
    try:
        parsed = json.loads(manifest_text)
    except json.JSONDecodeError as exc:
        raise ValueError(f"Invalid JSON in manifest.json: {error_message(exc)}") from exc
    return await validate_manifest(parsed)


async def parse_and_validate_manifest_from_bytes(manifest_data: bytes) -> McpbManifest:
    text = manifest_data.decode("utf-8")
    return await parse_and_validate_manifest_from_text(text)


def generate_extension_id(
    manifest: McpbManifest,
    prefix: str | None = None,
) -> str:
    def sanitize(s: str) -> str:
        s = s.lower()
        s = re.sub(r"\s+", "-", s)
        s = re.sub(r"[^a-z0-9\-_.]", "", s)
        s = re.sub(r"-+", "-", s)
        s = re.sub(r"^-+|-+$", "", s)
        return s

    sa = sanitize(manifest.author.name or "unknown")
    sn = sanitize(manifest.name or "extension")
    if prefix in ("local.unpacked", "local.dxt"):
        return f"{prefix}.{sa}.{sn}"
    return f"{sa}.{sn}"
