"""
Deep link protocol handler.

Migrated from: utils/deepLink/protocolHandler.ts + registerProtocol.ts
"""

from __future__ import annotations

import os
import platform
import subprocess
from collections.abc import Callable

from .parser import DeepLinkAction, parse_deep_link

# Handler callback type
DeepLinkHandler = Callable[[DeepLinkAction], None]

# Global handler
_handler: DeepLinkHandler | None = None


def register_deep_link_handler(handler: DeepLinkHandler) -> None:
    """
    Register a handler for deep links.

    Args:
        handler: Callback function
    """
    global _handler
    _handler = handler


def handle_deep_link(url: str) -> bool:
    """
    Handle a deep link URL.

    Args:
        url: Deep link URL

    Returns:
        True if handled successfully
    """
    action = parse_deep_link(url)

    if action is None:
        return False

    if _handler:
        _handler(action)
        return True

    return False


def register_protocol_handler() -> bool:
    """
    Register the deep link protocol handler with the OS.

    Returns:
        True if registered successfully
    """
    system = platform.system()

    if system == "Darwin":
        return _register_macos_handler()
    elif system == "Linux":
        return _register_linux_handler()
    elif system == "Windows":
        return _register_windows_handler()

    return False


def _register_macos_handler() -> bool:
    """Register on macOS using URL scheme."""
    # On macOS, this is typically done via Info.plist in the app bundle
    # For CLI, we can't register dynamically
    return False


def _register_linux_handler() -> bool:
    """Register on Linux using .desktop file."""
    try:
        home = os.path.expanduser("~")
        desktop_dir = os.path.join(home, ".local", "share", "applications")
        os.makedirs(desktop_dir, exist_ok=True)

        desktop_file = os.path.join(desktop_dir, "claude-cli-handler.desktop")

        # Get executable path
        import sys

        executable = sys.executable

        content = f"""[Desktop Entry]
Type=Application
Name=Claude CLI
Exec={executable} -m claude_code.entrypoints.main --deep-link %u
MimeType=x-scheme-handler/claude-cli;
NoDisplay=true
"""

        with open(desktop_file, "w") as f:
            f.write(content)

        # Register MIME handler
        subprocess.run(
            [
                "xdg-mime",
                "default",
                "claude-cli-handler.desktop",
                "x-scheme-handler/claude-cli",
            ],
            capture_output=True,
        )

        # Update MIME database
        subprocess.run(
            [
                "update-desktop-database",
                desktop_dir,
            ],
            capture_output=True,
        )

        return True

    except Exception:
        return False


def _register_windows_handler() -> bool:
    """Register on Windows using registry."""
    try:
        import sys
        import winreg

        executable = sys.executable

        # Create registry key
        key_path = r"Software\Classes\claude-cli"

        with winreg.CreateKey(winreg.HKEY_CURRENT_USER, key_path) as key:
            winreg.SetValue(key, "", winreg.REG_SZ, "URL:Claude CLI Protocol")
            winreg.SetValueEx(key, "URL Protocol", 0, winreg.REG_SZ, "")

        # Create command key
        command_path = rf"{key_path}\shell\open\command"
        command = f'"{executable}" -m claude_code.entrypoints.main --deep-link "%1"'

        with winreg.CreateKey(winreg.HKEY_CURRENT_USER, command_path) as key:
            winreg.SetValue(key, "", winreg.REG_SZ, command)

        return True

    except Exception:
        return False
