"""
Project snapshot sync for on-disk agent memory (``.claude/agent-memory-snapshots``).

Migrated from: tools/AgentTool/agentMemorySnapshot.ts
"""

from __future__ import annotations

import json
import os
import shutil
from pathlib import Path
from typing import Literal, TypedDict

from ...utils.debug import log_for_debugging

AgentMemoryScope = Literal["user", "project", "local"]

_SNAPSHOT_BASE = "agent-memory-snapshots"
_SNAPSHOT_JSON = "snapshot.json"
_SYNCED_JSON = ".snapshot-synced.json"


def _sanitize_agent_type(agent_type: str) -> str:
    return agent_type.replace(":", "-")


def _cwd() -> Path:
    return Path(os.getcwd())


def _memory_base_dir() -> Path:
    return Path(os.environ.get("CLAUDE_CONFIG_DIR", str(Path.home() / ".claude")))


def get_agent_memory_dir(agent_type: str, scope: AgentMemoryScope) -> Path:
    name = _sanitize_agent_type(agent_type)
    if scope == "project":
        return _cwd() / ".claude" / "agent-memory" / name
    if scope == "local":
        remote = os.environ.get("CLAUDE_CODE_REMOTE_MEMORY_DIR")
        if remote:
            return Path(remote) / "agent-memory-local" / name
        return _cwd() / ".claude" / "agent-memory-local" / name
    return _memory_base_dir() / "agent-memory" / name


def get_snapshot_dir_for_agent(agent_type: str) -> Path:
    return _cwd() / ".claude" / _SNAPSHOT_BASE / _sanitize_agent_type(agent_type)


class SnapshotCheckResult(TypedDict, total=False):
    action: Literal["none", "initialize", "prompt-update"]
    snapshotTimestamp: str


def _read_json(path: Path) -> dict[str, object] | None:
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return None


async def check_agent_memory_snapshot(
    agent_type: str,
    scope: AgentMemoryScope,
) -> SnapshotCheckResult:
    snap_path = get_snapshot_dir_for_agent(agent_type) / _SNAPSHOT_JSON
    meta = _read_json(snap_path)
    if not meta or not isinstance(meta.get("updatedAt"), str):
        return {"action": "none"}
    updated_at = str(meta["updatedAt"])
    local = get_agent_memory_dir(agent_type, scope)
    has_local = False
    try:
        for p in local.iterdir():
            if p.is_file() and p.suffix == ".md":
                has_local = True
                break
    except OSError:
        pass
    if not has_local:
        return {"action": "initialize", "snapshotTimestamp": updated_at}
    synced = _read_json(local / _SYNCED_JSON)
    synced_from = synced.get("syncedFrom") if isinstance(synced, dict) else None
    if not isinstance(synced_from, str):
        return {"action": "prompt-update", "snapshotTimestamp": updated_at}
    if updated_at > synced_from:
        return {"action": "prompt-update", "snapshotTimestamp": updated_at}
    return {"action": "none"}


def _copy_snapshot_to_local(agent_type: str, scope: AgentMemoryScope) -> None:
    snap_dir = get_snapshot_dir_for_agent(agent_type)
    dest = get_agent_memory_dir(agent_type, scope)
    dest.mkdir(parents=True, exist_ok=True)
    try:
        for p in snap_dir.iterdir():
            if p.is_file() and p.name != _SNAPSHOT_JSON:
                shutil.copy2(p, dest / p.name)
    except OSError as e:
        log_for_debugging(f"agent snapshot copy failed: {e}")


def _save_synced_meta(agent_type: str, scope: AgentMemoryScope, snapshot_ts: str) -> None:
    dest = get_agent_memory_dir(agent_type, scope)
    dest.mkdir(parents=True, exist_ok=True)
    path = dest / _SYNCED_JSON
    try:
        path.write_text(json.dumps({"syncedFrom": snapshot_ts}), encoding="utf-8")
    except OSError as e:
        log_for_debugging(f"agent snapshot synced meta failed: {e}")


async def initialize_from_snapshot(
    agent_type: str,
    scope: AgentMemoryScope,
    snapshot_timestamp: str,
) -> None:
    log_for_debugging(f"Initializing agent memory for {agent_type} from project snapshot")
    _copy_snapshot_to_local(agent_type, scope)
    _save_synced_meta(agent_type, scope, snapshot_timestamp)


async def replace_from_snapshot(
    agent_type: str,
    scope: AgentMemoryScope,
    snapshot_timestamp: str,
) -> None:
    local = get_agent_memory_dir(agent_type, scope)
    try:
        for p in local.iterdir():
            if p.is_file() and p.suffix == ".md":
                p.unlink(missing_ok=True)
    except OSError:
        pass
    await initialize_from_snapshot(agent_type, scope, snapshot_timestamp)


async def mark_snapshot_synced(
    agent_type: str,
    scope: AgentMemoryScope,
    snapshot_timestamp: str,
) -> None:
    _save_synced_meta(agent_type, scope, snapshot_timestamp)


__all__ = [
    "AgentMemoryScope",
    "SnapshotCheckResult",
    "check_agent_memory_snapshot",
    "get_agent_memory_dir",
    "get_snapshot_dir_for_agent",
    "initialize_from_snapshot",
    "mark_snapshot_synced",
    "replace_from_snapshot",
]
