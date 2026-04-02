"""
IDE MCP connection line status (ported from hooks/useIdeConnectionStatus.ts).
"""

from __future__ import annotations

from collections.abc import Mapping, Sequence
from dataclasses import dataclass
from typing import Literal

IdeStatus = Literal["connected", "disconnected", "pending"] | None


@dataclass(frozen=True)
class IdeConnectionResult:
    status: IdeStatus
    ide_name: str | None


def ide_connection_status(
    mcp_clients: Sequence[Mapping[str, object]] | None,
) -> IdeConnectionResult:
    if not mcp_clients:
        return IdeConnectionResult(status=None, ide_name=None)
    ide_client: Mapping[str, object] | None = None
    for c in mcp_clients:
        if c.get("name") == "ide":
            ide_client = c
            break
    if ide_client is None:
        return IdeConnectionResult(status=None, ide_name=None)
    raw_cfg = ide_client.get("config")
    cfg: Mapping[str, object] = raw_cfg if isinstance(raw_cfg, Mapping) else {}
    cfg_type = cfg.get("type")
    ide_name = None
    if cfg_type in ("sse-ide", "ws-ide"):
        raw_name = cfg.get("ideName", cfg.get("ide_name"))
        ide_name = str(raw_name) if raw_name is not None else None
    conn_type = ide_client.get("type")
    cs = str(conn_type) if conn_type is not None else ""
    if cs == "connected":
        return IdeConnectionResult(status="connected", ide_name=ide_name)
    if cs == "pending":
        return IdeConnectionResult(status="pending", ide_name=ide_name)
    return IdeConnectionResult(status="disconnected", ide_name=ide_name)
