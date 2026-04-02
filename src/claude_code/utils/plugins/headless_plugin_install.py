"""
Headless / CCR plugin installation (no AppState).

Migrated from: utils/plugins/headlessPluginInstall.ts
"""

from __future__ import annotations

import asyncio
import os
from typing import Any

from claude_code.services.analytics.events import log_event

from ..cleanup_registry import register_cleanup
from ..debug import log_for_debugging
from ..log import log_error
from .marketplace_manager import (
    clear_marketplaces_cache,
    get_declared_marketplaces,
    register_seed_marketplaces,
)
from .plugin_blocklist import detect_and_uninstall_delisted_plugins
from .plugin_loader import clear_plugin_cache
from .reconciler import reconcile_marketplaces
from .zip_cache import (
    cleanup_session_plugin_cache,
    get_zip_cache_marketplaces_dir,
    get_zip_cache_plugins_dir,
    is_marketplace_source_supported_by_zip_cache,
    is_plugin_zip_cache_enabled,
)
from .zip_cache_adapters import sync_marketplaces_to_zip_cache


async def install_plugins_for_headless() -> bool:
    zip_cache_mode = is_plugin_zip_cache_enabled()
    log_for_debugging(
        f"install_plugins_for_headless: starting{' (zip cache mode)' if zip_cache_mode else ''}",
    )

    seed_changed = await register_seed_marketplaces()
    if seed_changed:
        clear_marketplaces_cache()
        clear_plugin_cache("headless_plugin_install: seed marketplaces registered")

    if zip_cache_mode:

        def _mkdirs() -> None:
            os.makedirs(get_zip_cache_marketplaces_dir(), exist_ok=True)
            os.makedirs(get_zip_cache_plugins_dir(), exist_ok=True)

        await asyncio.to_thread(_mkdirs)

    declared_count = len(get_declared_marketplaces())
    metrics: dict[str, Any] = {"marketplaces_installed": 0, "delisted_count": 0}
    plugins_changed = seed_changed

    try:
        if declared_count == 0:
            log_for_debugging("install_plugins_for_headless: no marketplaces declared")
        else:

            def _skip(_name: str, source: dict[str, Any]) -> bool:
                return zip_cache_mode and not is_marketplace_source_supported_by_zip_cache(source)

            def _on_progress(event: dict[str, Any]) -> None:
                if event.get("type") == "installed":
                    log_for_debugging(
                        f"install_plugins_for_headless: installed marketplace {event.get('name')}",
                    )
                elif event.get("type") == "failed":
                    log_for_debugging(
                        "install_plugins_for_headless: failed to install marketplace "
                        f"{event.get('name')}: {event.get('error')}",
                    )

            reconcile_result = await reconcile_marketplaces(skip=_skip, on_progress=_on_progress)

            if reconcile_result.skipped:
                skipped_names = ", ".join(reconcile_result.skipped)
                log_for_debugging(
                    f"install_plugins_for_headless: skipped "
                    f"{len(reconcile_result.skipped)} marketplace(s) unsupported by zip cache: "
                    f"{skipped_names}",
                )

            marketplaces_changed = len(reconcile_result.installed) + len(reconcile_result.updated)
            if marketplaces_changed > 0:
                clear_marketplaces_cache()
                clear_plugin_cache("headless_plugin_install: marketplaces reconciled")
                plugins_changed = True
            metrics["marketplaces_installed"] = marketplaces_changed

        if zip_cache_mode:
            await sync_marketplaces_to_zip_cache()

        newly_delisted = await detect_and_uninstall_delisted_plugins()
        metrics["delisted_count"] = len(newly_delisted)
        if newly_delisted:
            plugins_changed = True

        if plugins_changed:
            clear_plugin_cache("headless_plugin_install: plugins changed")

        if zip_cache_mode:
            register_cleanup(cleanup_session_plugin_cache)

        return plugins_changed
    except Exception as exc:
        log_error(exc if isinstance(exc, BaseException) else Exception(str(exc)))
        return False
    finally:
        log_event("tengu_headless_plugin_install", metrics)


async def perform_background_plugin_installations() -> bool:
    """Alias for parity with TS naming in some call sites."""
    return await install_plugins_for_headless()


__all__ = ["install_plugins_for_headless", "perform_background_plugin_installations"]
