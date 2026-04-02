"""
Internal logging for Ant builds (Kubernetes namespace + permission context).

Migrated from: services/internalLogging.ts
"""

from __future__ import annotations

import functools
import json
from pathlib import Path
from typing import Any

from claude_code.services.analytics.events import log_event


def _is_ant_user() -> bool:
    import os

    return os.environ.get("USER_TYPE") == "ant"


@functools.lru_cache(maxsize=1)
def get_kubernetes_namespace() -> str | None:
    import os

    if os.environ.get("USER_TYPE") != "ant":
        return None
    namespace_path = Path("/var/run/secrets/kubernetes.io/serviceaccount/namespace")
    namespace_not_found = "namespace not found"
    try:
        return namespace_path.read_text(encoding="utf-8").strip()
    except OSError:
        return namespace_not_found


@functools.lru_cache(maxsize=1)
def get_container_id() -> str | None:
    import os

    if os.environ.get("USER_TYPE") != "ant":
        return None
    container_id_path = Path("/proc/self/mountinfo")
    container_id_not_found = "container ID not found"
    container_id_not_found_in_mountinfo = "container ID not found in mountinfo"
    try:
        mountinfo = container_id_path.read_text(encoding="utf-8").strip()
    except OSError:
        return container_id_not_found
    for line in mountinfo.split("\n"):
        for prefix in ("/docker/containers/", "/sandboxes/"):
            idx = line.find(prefix)
            if idx < 0:
                continue
            start = idx + len(prefix)
            candidate = line[start : start + 64]
            if len(candidate) == 64 and all(c in "0123456789abcdef" for c in candidate):
                return candidate
    return container_id_not_found_in_mountinfo


def log_permission_context_for_ants(
    tool_permission_context: dict[str, Any] | None,
    moment: str,
) -> None:
    import os

    if os.environ.get("USER_TYPE") != "ant":
        return
    log_event(
        "tengu_internal_record_permission_context",
        {
            "moment": moment,
            "namespace": get_kubernetes_namespace(),
            "toolPermissionContext": json.dumps(tool_permission_context or {}),
            "containerId": get_container_id(),
        },
    )
