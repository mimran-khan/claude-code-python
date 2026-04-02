"""
Debug dump of recent API requests (ant-only) and JSONL prompt dumps.

Migrated from: services/api/dumpPrompts.ts
"""

from __future__ import annotations

import hashlib
import json
import os
import threading
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

from ...utils.env_utils import get_claude_config_home_dir

_MAX_CACHED = 5
_cached_api_requests: list[dict[str, Any]] = []
_cache_lock = threading.Lock()
_dump_state: dict[str, dict[str, Any]] = {}
_state_lock = threading.Lock()


def get_last_api_requests() -> list[dict[str, Any]]:
    with _cache_lock:
        return list(_cached_api_requests)


def clear_api_request_cache() -> None:
    with _cache_lock:
        _cached_api_requests.clear()


def clear_dump_state(agent_id_or_session_id: str) -> None:
    with _state_lock:
        _dump_state.pop(agent_id_or_session_id, None)


def clear_all_dump_state() -> None:
    with _state_lock:
        _dump_state.clear()


def add_api_request_to_cache(request_data: object) -> None:
    if os.environ.get("USER_TYPE") != "ant":
        return
    with _cache_lock:
        _cached_api_requests.append(
            {
                "timestamp": datetime.now(tz=UTC).isoformat(),
                "request": request_data,
            }
        )
        while len(_cached_api_requests) > _MAX_CACHED:
            _cached_api_requests.pop(0)


def get_dump_prompts_path(agent_id_or_session_id: str | None = None) -> str:
    sid = agent_id_or_session_id or os.environ.get("CLAUDE_SESSION_ID", "default")
    return str(Path(get_claude_config_home_dir()) / "dump-prompts" / f"{sid}.jsonl")


def _hash_str(s: str) -> str:
    return hashlib.sha256(s.encode()).hexdigest()


def maybe_dump_prompts(agent_id: str, payload: dict[str, Any]) -> None:
    """Append one JSON line when USER_TYPE=ant and payload changed (simplified)."""
    if os.environ.get("USER_TYPE") != "ant":
        return
    path = Path(get_dump_prompts_path(agent_id))
    path.parent.mkdir(parents=True, exist_ok=True)
    line = json.dumps({"ts": datetime.now(tz=UTC).isoformat(), "payload": payload}) + "\n"
    with path.open("a", encoding="utf-8") as f:
        f.write(line)
