"""Dynamic MCP headers via headersHelper command.

Migrated from: services/mcp/headersHelper.ts (simplified: JSON stdout contract).
"""

from __future__ import annotations

import asyncio
import json
import os
import shlex
from dataclasses import dataclass
from typing import Any

import structlog

logger = structlog.get_logger(__name__)


@dataclass
class HeadersHelperConfig:
    headers_helper: str
    scope: str | None = None


async def get_mcp_headers_from_helper(
    server_name: str,
    config: HeadersHelperConfig,
    *,
    trust_accepted: bool = True,
    non_interactive: bool = False,
) -> dict[str, str] | None:
    if not config.headers_helper:
        return None
    if config.scope in ("project", "local") and not non_interactive and not trust_accepted:
        logger.error(
            "mcp_headers_helper_trust",
            server=server_name,
            message="headersHelper before workspace trust",
        )
        return None
    try:
        parts = shlex.split(config.headers_helper, posix=os.name != "nt")
        proc = await asyncio.create_subprocess_exec(
            *parts,
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE,
            cwd=os.getcwd(),
        )
        out_b, err_b = await asyncio.wait_for(proc.communicate(), timeout=30.0)
    except Exception as exc:
        logger.warning("mcp_headers_helper_failed", server=server_name, error=str(exc))
        return None
    if proc.returncode != 0:
        logger.warning(
            "mcp_headers_helper_exit",
            server=server_name,
            code=proc.returncode,
            stderr=err_b.decode(errors="replace")[:500],
        )
        return None
    try:
        data: Any = json.loads(out_b.decode() or "{}")
    except json.JSONDecodeError:
        return None
    if not isinstance(data, dict):
        return None
    return {str(k): str(v) for k, v in data.items()}
