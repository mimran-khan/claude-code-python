"""
Computer-use utilities (desktop automation MCP host, locks, gates).

Migrated from: utils/computerUse/*.ts (plus appNames, escHotkey, swiftLoader).
"""

from __future__ import annotations

from .app_names import filter_apps_for_description
from .cleanup import ComputerUseCleanupContext, cleanup_computer_use_after_turn
from .common import (
    CLI_CU_CAPABILITIES,
    CLI_HOST_BUNDLE_ID,
    COMPUTER_USE_MCP_SERVER_NAME,
    get_cli_cu_capabilities,
    get_terminal_bundle_id,
    is_computer_use_mcp_server,
)
from .drain_run_loop import drain_run_loop, release_pump, retain_pump
from .esc_hotkey import notify_expected_escape, register_esc_hotkey, unregister_esc_hotkey
from .executor import CliExecutorOptions, create_cli_executor, unhide_computer_use_apps
from .gates import (
    ComputerUseGate,
    CuSubGates,
    check_accessibility_permission,
    check_computer_use_gates,
    get_chicago_coordinate_mode,
    get_chicago_enabled,
    get_chicago_sub_gates,
    get_subscription_type,
    is_computer_use_available,
    is_computer_use_enabled,
)
from .host_adapter import get_computer_use_host_adapter
from .input_loader import ComputerUseInputAPI, require_computer_use_input
from .lock import (
    AcquireResult,
    CheckResult,
    check_computer_use_lock,
    is_lock_held_locally,
    release_computer_use_lock,
    try_acquire_computer_use_lock,
)
from .mcp_server import (
    build_computer_use_tools,
    create_computer_use_mcp_server_for_cli,
    enable_configs,
    run_computer_use_mcp_server,
    try_get_installed_app_names,
)
from .setup import setup_computer_use_mcp
from .swift_loader import ComputerUseNativeAPI, require_computer_use_swift, target_image_size
from .types import ComputerExecutor, ComputerUseHostAdapter, Logger

__all__ = [
    "CLI_CU_CAPABILITIES",
    "CLI_HOST_BUNDLE_ID",
    "COMPUTER_USE_MCP_SERVER_NAME",
    "AcquireResult",
    "CheckResult",
    "CliExecutorOptions",
    "ComputerExecutor",
    "ComputerUseCleanupContext",
    "ComputerUseGate",
    "ComputerUseHostAdapter",
    "ComputerUseInputAPI",
    "ComputerUseNativeAPI",
    "CuSubGates",
    "Logger",
    "build_computer_use_tools",
    "check_accessibility_permission",
    "check_computer_use_gates",
    "check_computer_use_lock",
    "cleanup_computer_use_after_turn",
    "create_cli_executor",
    "create_computer_use_mcp_server_for_cli",
    "drain_run_loop",
    "enable_configs",
    "filter_apps_for_description",
    "get_chicago_coordinate_mode",
    "get_chicago_enabled",
    "get_chicago_sub_gates",
    "get_cli_cu_capabilities",
    "get_computer_use_host_adapter",
    "get_subscription_type",
    "get_terminal_bundle_id",
    "is_computer_use_available",
    "is_computer_use_enabled",
    "is_computer_use_mcp_server",
    "is_lock_held_locally",
    "notify_expected_escape",
    "register_esc_hotkey",
    "release_computer_use_lock",
    "release_pump",
    "require_computer_use_input",
    "require_computer_use_swift",
    "retain_pump",
    "run_computer_use_mcp_server",
    "setup_computer_use_mcp",
    "target_image_size",
    "try_acquire_computer_use_lock",
    "try_get_installed_app_names",
    "unhide_computer_use_apps",
    "unregister_esc_hotkey",
]
