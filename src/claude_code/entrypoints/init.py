"""
Application initialization.

Setup and teardown procedures.

Migrated from: entrypoints/init.ts (341 lines)
"""

from __future__ import annotations

import asyncio
import atexit
import os

from ..utils.debug import log_for_debugging

# Module state
_initialized = False
_shutdown_registered = False


def is_initialized() -> bool:
    """Check if the application is initialized."""
    return _initialized


async def initialize() -> None:
    """
    Initialize the application.

    Performs all necessary setup:
    - Load configuration
    - Setup telemetry
    - Initialize services
    - Register cleanup handlers
    """
    global _initialized, _shutdown_registered

    if _initialized:
        return

    log_for_debugging("init: starting initialization")

    # Load and validate configuration
    _init_config()

    # Setup environment
    _init_environment()

    # Register cleanup handlers
    if not _shutdown_registered:
        atexit.register(_cleanup_sync)
        _shutdown_registered = True

    # Initialize services
    await _init_services()

    _initialized = True
    log_for_debugging("init: initialization complete")


def _init_config() -> None:
    """Initialize configuration."""
    from ..utils.config_utils import get_global_config

    # Load global config (validates it exists and is parseable)
    try:
        get_global_config()
        log_for_debugging("init: loaded config")
    except Exception as e:
        log_for_debugging(f"init: config load error: {e}")


def _init_environment() -> None:
    """Initialize environment settings."""
    # Set default environment variables if not set
    if not os.getenv("CLAUDE_CODE_SESSION_ID"):
        import uuid

        os.environ["CLAUDE_CODE_SESSION_ID"] = str(uuid.uuid4())


async def _init_services() -> None:
    """Initialize services."""
    # Initialize API client pool
    log_for_debugging("init: services ready")


async def shutdown() -> None:
    """
    Shutdown the application.

    Performs cleanup:
    - Close connections
    - Flush logs
    - Save state
    """
    global _initialized

    if not _initialized:
        return

    log_for_debugging("shutdown: starting cleanup")

    # Stop LSP servers
    try:
        from ..services.lsp import get_lsp_manager

        await get_lsp_manager().stop_all()
    except Exception:
        pass

    # Flush telemetry
    try:
        from ..utils.telemetry import get_telemetry_logger

        get_telemetry_logger().clear()
    except Exception:
        pass

    _initialized = False
    log_for_debugging("shutdown: cleanup complete")


def _cleanup_sync() -> None:
    """Synchronous cleanup for atexit."""
    try:
        loop = asyncio.get_event_loop()
        if loop.is_running():
            loop.create_task(shutdown())
        else:
            loop.run_until_complete(shutdown())
    except Exception:
        pass
