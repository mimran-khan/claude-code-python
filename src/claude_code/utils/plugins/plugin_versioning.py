"""Plugin version strings from manifest, git, or fallbacks. Migrated from pluginVersioning.ts."""

from __future__ import annotations

import asyncio
import hashlib
import subprocess
from typing import Any

from ..debug import log_for_debugging


async def calculate_plugin_version(
    plugin_id: str,
    source: dict[str, Any],
    manifest: Any | None = None,
    install_path: str | None = None,
    provided_version: str | None = None,
    git_commit_sha: str | None = None,
) -> str:
    if manifest is not None and getattr(manifest, "version", None):
        log_for_debugging(f"Using manifest version for {plugin_id}: {manifest.version}")
        return str(manifest.version)
    if provided_version:
        log_for_debugging(f"Using provided version for {plugin_id}: {provided_version}")
        return provided_version
    if git_commit_sha:
        short = git_commit_sha[:12]
        if isinstance(source, dict) and source.get("source") == "git-subdir":
            path = str(source.get("path") or "")
            norm = path.replace("\\", "/").lstrip("./").rstrip("/")
            digest = hashlib.sha256(norm.encode()).hexdigest()[:8]
            return f"{short}-{digest}"
        return short
    if install_path:

        def _git_rev() -> str | None:
            try:
                out = subprocess.run(
                    ["git", "-C", install_path, "rev-parse", "HEAD"],
                    capture_output=True,
                    text=True,
                    timeout=10,
                    check=False,
                )
                if out.returncode == 0 and out.stdout.strip():
                    return out.stdout.strip()[:12]
            except (OSError, subprocess.TimeoutExpired):
                pass
            return None

        sha = await asyncio.to_thread(_git_rev)
        if sha:
            log_for_debugging(f"Using git SHA for {plugin_id}: {sha}")
            return sha
    log_for_debugging(f"Unknown version for {plugin_id}")
    return "unknown"


__all__ = ["calculate_plugin_version"]
