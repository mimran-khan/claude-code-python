"""
Reconcile known_marketplaces.json with settings intent.

Migrated from: utils/plugins/reconciler.ts
"""

from __future__ import annotations

import asyncio
import os
from collections.abc import Callable
from dataclasses import dataclass, field
from typing import Any, Literal

from ...bootstrap.state import get_original_cwd
from ..debug import log_for_debugging
from ..errors import error_message
from ..git import find_canonical_git_root
from ..log import log_error
from .marketplace_helpers import is_local_marketplace_source
from .marketplace_manager import (
    DeclaredMarketplace,
    add_marketplace_source,
    get_declared_marketplaces,
    load_known_marketplaces_config_safe,
)


@dataclass
class MarketplaceDiff:
    missing: list[str] = field(default_factory=list)
    source_changed: list[dict[str, Any]] = field(default_factory=list)
    up_to_date: list[str] = field(default_factory=list)


def normalize_source(source: dict[str, Any], project_root: str | None) -> dict[str, Any]:
    out = dict(source)
    if source.get("source") in ("directory", "file"):
        path = source.get("path")
        if isinstance(path, str) and not os.path.isabs(path):
            base = project_root or os.getcwd()
            canonical = find_canonical_git_root(base)
            root = canonical or base
            out["path"] = os.path.normpath(os.path.join(root, path))
    return out


def diff_marketplaces(
    declared: dict[str, DeclaredMarketplace],
    materialized: dict[str, Any],
    *,
    project_root: str | None = None,
) -> MarketplaceDiff:
    missing: list[str] = []
    source_changed: list[dict[str, Any]] = []
    up_to_date: list[str] = []

    for name, intent in declared.items():
        state = materialized.get(name)
        normalized_intent = normalize_source(intent.source, project_root)

        if not state:
            missing.append(name)
        elif intent.source_is_fallback:
            up_to_date.append(name)
        elif not isinstance(state, dict):
            missing.append(name)
        elif normalized_intent != state.get("source"):
            source_changed.append(
                {
                    "name": name,
                    "declaredSource": normalized_intent,
                    "materializedSource": state.get("source"),
                }
            )
        else:
            up_to_date.append(name)

    return MarketplaceDiff(
        missing=missing,
        source_changed=source_changed,
        up_to_date=up_to_date,
    )


ReconcileProgressEvent = dict[str, Any]


@dataclass
class ReconcileResult:
    installed: list[str] = field(default_factory=list)
    updated: list[str] = field(default_factory=list)
    failed: list[dict[str, str]] = field(default_factory=list)
    up_to_date: list[str] = field(default_factory=list)
    skipped: list[str] = field(default_factory=list)


async def reconcile_marketplaces(
    *,
    skip: Callable[[str, dict[str, Any]], bool] | None = None,
    on_progress: Callable[[ReconcileProgressEvent], None] | None = None,
) -> ReconcileResult:
    declared = get_declared_marketplaces()
    if not declared:
        return ReconcileResult()

    try:
        materialized = await load_known_marketplaces_config_safe()
    except Exception as exc:
        log_error(exc)
        materialized = {}

    diff = diff_marketplaces(
        declared,
        materialized,
        project_root=get_original_cwd(),
    )

    work: list[tuple[str, dict[str, Any], Literal["install", "update"]]] = []
    for name in diff.missing:
        work.append((name, normalize_source(declared[name].source, get_original_cwd()), "install"))
    for item in diff.source_changed:
        name = str(item["name"])
        work.append(
            (name, normalize_source(item["declaredSource"], get_original_cwd()), "update"),
        )

    skipped: list[str] = []
    to_process: list[tuple[str, dict[str, Any], Literal["install", "update"]]] = []
    for name, source, action in work:
        if skip and skip(name, source):
            skipped.append(name)
            continue
        if action == "update" and is_local_marketplace_source(source):
            exists = await asyncio.to_thread(os.path.exists, str(source.get("path", "")))
            if not exists:
                log_for_debugging(
                    f"[reconcile] '{name}' declared path does not exist; keeping materialized entry",
                )
                skipped.append(name)
                continue
        to_process.append((name, source, action))

    if not to_process:
        return ReconcileResult(up_to_date=diff.up_to_date, skipped=skipped)

    log_for_debugging(
        f"[reconcile] {len(to_process)} marketplace(s): " + ", ".join(f"{n}({a})" for n, _s, a in to_process),
    )

    installed: list[str] = []
    updated: list[str] = []
    failed: list[dict[str, str]] = []

    for i, (name, source, action) in enumerate(to_process):
        if on_progress:
            on_progress(
                {
                    "type": "installing",
                    "name": name,
                    "action": action,
                    "index": i + 1,
                    "total": len(to_process),
                }
            )
        try:
            result = await add_marketplace_source(source)
            if action == "install":
                installed.append(name)
            else:
                updated.append(name)
            if on_progress:
                on_progress(
                    {
                        "type": "installed",
                        "name": name,
                        "alreadyMaterialized": result.already_materialized,
                    }
                )
        except Exception as exc:
            msg = error_message(exc)
            failed.append({"name": name, "error": msg})
            if on_progress:
                on_progress({"type": "failed", "name": name, "error": msg})
            log_error(exc)

    return ReconcileResult(
        installed=installed,
        updated=updated,
        failed=failed,
        up_to_date=diff.up_to_date,
        skipped=skipped,
    )


__all__ = [
    "MarketplaceDiff",
    "ReconcileResult",
    "diff_marketplaces",
    "normalize_source",
    "reconcile_marketplaces",
]
