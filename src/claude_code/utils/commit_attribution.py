"""
Git commit attribution: internal repo detection, surface keys, file tracking.

Migrated from: utils/commitAttribution.ts (core logic; git calls via asyncio subprocess).
"""

from __future__ import annotations

import asyncio
import hashlib
import os
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Literal

INTERNAL_MODEL_REPOS: tuple[str, ...] = (
    "github.com:anthropics/claude-cli-internal",
    "github.com/anthropics/claude-cli-internal",
    "github.com:anthropics/anthropic",
    "github.com/anthropics/anthropic",
    "github.com:anthropics/apps",
    "github.com/anthropics/apps",
    "github.com:anthropics/casino",
    "github.com/anthropics/casino",
    "github.com:anthropics/dbt",
    "github.com/anthropics/dbt",
    "github.com:anthropics/dotfiles",
    "github.com/anthropics/dotfiles",
    "github.com:anthropics/terraform-config",
    "github.com/anthropics/terraform-config",
    "github.com:anthropics/hex-export",
    "github.com/anthropics/hex-export",
    "github.com:anthropics/feedback-v2",
    "github.com/anthropics/feedback-v2",
    "github.com:anthropics/labs",
    "github.com/anthropics/labs",
    "github.com:anthropics/argo-rollouts",
    "github.com/anthropics/argo-rollouts",
    "github.com:anthropics/starling-configs",
    "github.com/anthropics/starling-configs",
    "github.com:anthropics/ts-tools",
    "github.com/anthropics/ts-tools",
    "github.com:anthropics/ts-capsules",
    "github.com/anthropics/ts-capsules",
    "github.com:anthropics/feldspar-testing",
    "github.com/anthropics/feldspar-testing",
    "github.com:anthropics/trellis",
    "github.com/anthropics/trellis",
    "github.com:anthropics/claude-for-hiring",
    "github.com/anthropics/claude-for-hiring",
    "github.com:anthropics/forge-web",
    "github.com/anthropics/forge-web",
    "github.com:anthropics/infra-manifests",
    "github.com/anthropics/infra-manifests",
    "github.com:anthropics/mycro_manifests",
    "github.com/anthropics/mycro_manifests",
    "github.com:anthropics/mycro_configs",
    "github.com/anthropics/mycro_configs",
    "github.com:anthropics/mobile-apps",
    "github.com/anthropics/mobile-apps",
)

_repo_class_cache: Literal["internal", "external", "none"] | None = None
_is_internal_model_repo_lock = asyncio.Lock()


def get_repo_class_cached() -> Literal["internal", "external", "none"] | None:
    return _repo_class_cache


def is_internal_model_repo_cached() -> bool:
    return _repo_class_cache == "internal"


def sanitize_model_name(short_name: str) -> str:
    s = short_name
    if "opus-4-6" in s:
        return "claude-opus-4-6"
    if "opus-4-5" in s:
        return "claude-opus-4-5"
    if "opus-4-1" in s:
        return "claude-opus-4-1"
    if "opus-4" in s:
        return "claude-opus-4"
    if "sonnet-4-6" in s:
        return "claude-sonnet-4-6"
    if "sonnet-4-5" in s:
        return "claude-sonnet-4-5"
    if "sonnet-4" in s:
        return "claude-sonnet-4"
    if "sonnet-3-7" in s:
        return "claude-sonnet-3-7"
    if "haiku-4-5" in s:
        return "claude-haiku-4-5"
    if "haiku-3-5" in s:
        return "claude-haiku-3-5"
    return "claude"


def sanitize_surface_key(surface_key: str) -> str:
    idx = surface_key.rfind("/")
    if idx == -1:
        return surface_key
    surface = surface_key[:idx]
    model = surface_key[idx + 1 :]
    return f"{surface}/{sanitize_model_name(model)}"


def get_client_surface() -> str:
    return os.environ.get("CLAUDE_CODE_ENTRYPOINT") or "cli"


def build_surface_key(surface: str, model: str) -> str:
    from .model.model import get_canonical_name

    return f"{surface}/{get_canonical_name(model)}"


def compute_content_hash(content: str) -> str:
    return hashlib.sha256(content.encode("utf-8")).hexdigest()


@dataclass
class FileAttributionState:
    content_hash: str
    claude_contribution: int
    mtime: float


@dataclass
class AttributionState:
    file_states: dict[str, FileAttributionState] = field(default_factory=dict)
    session_baselines: dict[str, dict[str, Any]] = field(default_factory=dict)
    surface: str = field(default_factory=get_client_surface)
    starting_head_sha: str | None = None
    prompt_count: int = 0
    prompt_count_at_last_commit: int = 0
    permission_prompt_count: int = 0
    permission_prompt_count_at_last_commit: int = 0
    escape_count: int = 0
    escape_count_at_last_commit: int = 0


def create_empty_attribution_state() -> AttributionState:
    return AttributionState(surface=get_client_surface())


def normalize_file_path(file_path: str, repo_root: str) -> str:
    p = Path(file_path)
    root = Path(repo_root)
    try:
        p = p.resolve()
        root = root.resolve()
    except OSError:
        pass
    try:
        rel = os.path.relpath(str(p), str(root))
        return rel.replace(os.sep, "/")
    except ValueError:
        return file_path


def expand_file_path(file_path: str, repo_root: str) -> str:
    if os.path.isabs(file_path):
        return file_path
    return str(Path(repo_root) / file_path)


async def get_remote_url_for_dir(cwd: str) -> str | None:
    proc = await asyncio.create_subprocess_exec(
        "git",
        "remote",
        "get-url",
        "origin",
        cwd=cwd,
        stdout=asyncio.subprocess.PIPE,
        stderr=asyncio.subprocess.DEVNULL,
    )
    out, _ = await proc.communicate()
    if proc.returncode != 0 or not out:
        return None
    return out.decode("utf-8", errors="replace").strip()


async def is_internal_model_repo(repo_root: str | None = None) -> bool:
    global _repo_class_cache
    if _repo_class_cache is not None:
        return _repo_class_cache == "internal"
    async with _is_internal_model_repo_lock:
        if _repo_class_cache is not None:
            return _repo_class_cache == "internal"
        cwd = repo_root or os.getcwd()
        remote = await get_remote_url_for_dir(cwd)
        if not remote:
            _repo_class_cache = "none"
            return False
        internal = any(repo in remote for repo in INTERNAL_MODEL_REPOS)
        _repo_class_cache = "internal" if internal else "external"
        return internal


def _compute_file_modification_state(
    file_states: dict[str, FileAttributionState],
    file_path: str,
    old_content: str,
    new_content: str,
    mtime: float,
    repo_root: str,
) -> FileAttributionState | None:
    normalized_path = normalize_file_path(file_path, repo_root)
    if old_content == "" or new_content == "":
        claude_contribution = len(new_content) if old_content == "" else len(old_content)
    else:
        min_len = min(len(old_content), len(new_content))
        prefix_end = 0
        while prefix_end < min_len and old_content[prefix_end] == new_content[prefix_end]:
            prefix_end += 1
        suffix_len = 0
        while (
            suffix_len < min_len - prefix_end
            and old_content[len(old_content) - 1 - suffix_len] == new_content[len(new_content) - 1 - suffix_len]
        ):
            suffix_len += 1
        old_changed = len(old_content) - prefix_end - suffix_len
        new_changed = len(new_content) - prefix_end - suffix_len
        claude_contribution = max(old_changed, new_changed)
    existing = file_states.get(normalized_path)
    prior = existing.claude_contribution if existing else 0
    return FileAttributionState(
        content_hash=compute_content_hash(new_content),
        claude_contribution=prior + claude_contribution,
        mtime=mtime,
    )


def track_file_modification(
    state: AttributionState,
    file_path: str,
    old_content: str,
    new_content: str,
    repo_root: str,
    mtime: float | None = None,
) -> AttributionState:
    mt = mtime if mtime is not None else __import__("time").time() * 1000
    normalized = normalize_file_path(file_path, repo_root)
    new_state = _compute_file_modification_state(state.file_states, file_path, old_content, new_content, mt, repo_root)
    fs = dict(state.file_states)
    fs[normalized] = new_state
    return AttributionState(
        file_states=fs,
        session_baselines=dict(state.session_baselines),
        surface=state.surface,
        starting_head_sha=state.starting_head_sha,
        prompt_count=state.prompt_count,
        prompt_count_at_last_commit=state.prompt_count_at_last_commit,
        permission_prompt_count=state.permission_prompt_count,
        permission_prompt_count_at_last_commit=state.permission_prompt_count_at_last_commit,
        escape_count=state.escape_count,
        escape_count_at_last_commit=state.escape_count_at_last_commit,
    )
