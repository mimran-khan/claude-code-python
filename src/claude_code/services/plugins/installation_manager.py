"""
Background plugin installation manager.

Handles automatic installation of plugins and marketplaces
from trusted sources without blocking startup.

Migrated from: services/plugins/PluginInstallationManager.ts (185 lines)
"""

from __future__ import annotations

from collections.abc import Callable
from dataclasses import dataclass
from typing import Any, Literal

from ...utils.debug import log_for_debugging
from ...utils.log import log_error

MarketplaceStatus = Literal["pending", "installing", "installed", "failed"]


@dataclass
class MarketplaceInstallStatus:
    """Status of a marketplace installation."""

    name: str
    status: MarketplaceStatus
    error: str | None = None


@dataclass
class PluginInstallStatus:
    """Status of a plugin installation."""

    plugin_id: str
    status: MarketplaceStatus
    error: str | None = None


@dataclass
class InstallationStatus:
    """Overall installation status."""

    marketplaces: list[MarketplaceInstallStatus]
    plugins: list[PluginInstallStatus]


@dataclass
class ReconcileResult:
    """Result of marketplace reconciliation."""

    installed: list[str]
    updated: list[str]
    failed: list[str]
    up_to_date: list[str]


def update_marketplace_status(
    set_app_state: Callable[[Any], None],
    name: str,
    status: MarketplaceStatus,
    error: str | None = None,
) -> None:
    """Update marketplace installation status in app state."""
    # This would update the app state
    # Stub implementation
    pass


async def perform_background_plugin_installations(
    set_app_state: Callable[[Any], None],
) -> None:
    """
    Perform background plugin startup checks and installations.

    This handles marketplace reconciliation and maps onProgress
    events to AppState updates for the UI.

    After marketplaces are reconciled:
    - New installs -> auto-refresh plugins
    - Updates only -> set needsRefresh, show notification

    Args:
        set_app_state: Function to update app state
    """
    log_for_debugging("perform_background_plugin_installations called")

    try:
        # Get declared marketplaces
        pending_names: list[str] = []

        # Initialize AppState with pending status
        # This is a stub - actual implementation would compute diff

        if len(pending_names) == 0:
            return

        log_for_debugging(f"Installing {len(pending_names)} marketplace(s) in background")

        # Reconcile marketplaces
        result = ReconcileResult(
            installed=[],
            updated=[],
            failed=[],
            up_to_date=[],
        )

        # Log metrics
        metrics = {
            "installed_count": len(result.installed),
            "updated_count": len(result.updated),
            "failed_count": len(result.failed),
            "up_to_date_count": len(result.up_to_date),
        }

        log_for_debugging(f"Background installation complete: {metrics}")

    except Exception as error:
        log_error(error)


async def reconcile_marketplaces(
    on_progress: Callable[[dict[str, Any]], None] | None = None,
) -> ReconcileResult:
    """
    Reconcile marketplaces between declared and materialized state.

    Args:
        on_progress: Optional callback for progress events

    Returns:
        ReconcileResult with counts of each operation type
    """
    # Stub implementation
    return ReconcileResult(
        installed=[],
        updated=[],
        failed=[],
        up_to_date=[],
    )


def clear_marketplace_caches() -> None:
    """Clear all marketplace caches."""
    # Stub implementation
    pass


def clear_plugin_cache(reason: str) -> None:
    """Clear the plugin cache."""
    log_for_debugging(f"Clearing plugin cache: {reason}")
    # Stub implementation
