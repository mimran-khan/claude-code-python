"""Crash-recovery pointer for Remote Control (ported from bridge/bridgePointer.ts)."""

from __future__ import annotations

import json
import logging
import time
from pathlib import Path
from typing import Any, Literal

from pydantic import BaseModel, Field

# TODO: get_projects_dir, sanitize_path, get_worktree_paths_portable

logger = logging.getLogger(__name__)
MAX_WORKTREE_FANOUT = 50
BRIDGE_POINTER_TTL_MS = 4 * 60 * 60 * 1000


class BridgePointer(BaseModel):
    session_id: str = Field(alias="sessionId")
    environment_id: str = Field(alias="environmentId")
    source: Literal["standalone", "repl"]

    model_config = {"populate_by_name": True}


def _sanitize_path(d: str) -> str:
    return d.replace("\\", "/")


def get_bridge_pointer_path(dir: str) -> Path:
    # TODO: join(get_projects_dir(), sanitize_path(dir), 'bridge-pointer.json')
    base = Path.home() / ".claude" / "projects"
    return base / _sanitize_path(dir).lstrip("/") / "bridge-pointer.json"


def _safe_json_parse(raw: str) -> Any:
    try:
        return json.loads(raw)
    except Exception:
        return None


async def write_bridge_pointer(dir: str, pointer: BridgePointer) -> None:
    path = get_bridge_pointer_path(dir)
    try:
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(pointer.model_dump_json(by_alias=True), encoding="utf-8")
        logger.debug("[bridge:pointer] wrote %s", path)
    except Exception as e:
        logger.warning("[bridge:pointer] write failed: %s", e)


async def read_bridge_pointer(dir: str) -> dict[str, Any] | None:
    path = get_bridge_pointer_path(dir)
    try:
        st = path.stat()
        mtime_ms = int(st.st_mtime * 1000)
        raw = path.read_text(encoding="utf-8")
    except Exception:
        return None
    data = _safe_json_parse(raw)
    try:
        p = BridgePointer.model_validate(data)
    except Exception:
        logger.debug("[bridge:pointer] invalid schema, clearing: %s", path)
        await clear_bridge_pointer(dir)
        return None
    age_ms = max(0, int(time.time() * 1000) - mtime_ms)
    if age_ms > BRIDGE_POINTER_TTL_MS:
        logger.debug("[bridge:pointer] stale (>4h mtime), clearing: %s", path)
        await clear_bridge_pointer(dir)
        return None
    d = p.model_dump(by_alias=True)
    d["ageMs"] = age_ms
    return d


async def read_bridge_pointer_across_worktrees(dir: str) -> dict[str, Any] | None:
    here = await read_bridge_pointer(dir)
    if here:
        return {"pointer": here, "dir": dir}
    # TODO: get_worktree_paths_portable(dir) and fanout
    return None


async def clear_bridge_pointer(dir: str) -> None:
    path = get_bridge_pointer_path(dir)
    try:
        path.unlink()
        logger.debug("[bridge:pointer] cleared %s", path)
    except FileNotFoundError:
        pass
    except Exception as e:
        logger.warning("[bridge:pointer] clear failed: %s", e)
