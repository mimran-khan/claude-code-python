"""
Terminal launcher for deep links.

Migrated from: utils/deepLink/terminalLauncher.ts + terminalPreference.ts
"""

from __future__ import annotations

import os
import platform
import shutil
import subprocess

from .parser import DeepLinkAction

# Terminal preference key
TERMINAL_PREFERENCE_KEY = "claude_code_terminal"


def get_terminal_preference() -> str | None:
    """
    Get the user's preferred terminal.

    Returns:
        Terminal identifier or None
    """
    return os.getenv(TERMINAL_PREFERENCE_KEY)


def set_terminal_preference(terminal: str) -> None:
    """
    Set the user's preferred terminal.

    Args:
        terminal: Terminal identifier
    """
    os.environ[TERMINAL_PREFERENCE_KEY] = terminal


def launch_terminal_with_deep_link(action: DeepLinkAction) -> bool:
    """
    Launch a terminal with the deep link action.

    Args:
        action: Deep link action

    Returns:
        True if launched successfully
    """
    system = platform.system()

    if system == "Darwin":
        return _launch_macos_terminal(action)
    elif system == "Linux":
        return _launch_linux_terminal(action)
    elif system == "Windows":
        return _launch_windows_terminal(action)

    return False


def _escape_single_quote(s: str) -> str:
    """Escape single quotes for shell."""
    return s.replace("'", "'\\''")


def _build_command(action: DeepLinkAction) -> str:
    """Build the claude-code command."""
    import sys

    parts = [sys.executable, "-m", "claude_code.entrypoints.main"]

    if action.query:
        parts.append("--prefill")
        parts.append(f"'{_escape_single_quote(action.query)}'")

    if action.cwd:
        parts.append("--cwd")
        parts.append(f"'{_escape_single_quote(action.cwd)}'")

    return " ".join(parts)


def _launch_macos_terminal(action: DeepLinkAction) -> bool:
    """Launch on macOS."""
    command = _build_command(action)
    preference = get_terminal_preference()

    # Try preferred terminal first
    terminals = [
        ("Terminal.app", _launch_macos_terminal_app),
        ("iTerm.app", _launch_macos_iterm),
        ("Warp", _launch_macos_warp),
        ("kitty", _launch_generic_terminal),
    ]

    if preference:
        terminals.sort(key=lambda t: 0 if preference in t[0] else 1)

    for _name, launcher in terminals:
        try:
            if launcher(command, action.cwd):
                return True
        except Exception:
            continue

    return False


def _launch_macos_terminal_app(command: str, cwd: str | None) -> bool:
    """Launch in Terminal.app."""
    escaped_cmd = command.replace('"', '\\"')
    script = f'''
tell application "Terminal"
    activate
    do script "{escaped_cmd}"
end tell
'''
    try:
        subprocess.run(["osascript", "-e", script], capture_output=True)
        return True
    except Exception:
        return False


def _launch_macos_iterm(command: str, cwd: str | None) -> bool:
    """Launch in iTerm2."""
    escaped_cmd = command.replace('"', '\\"')
    script = f'''
tell application "iTerm"
    activate
    create window with default profile
    tell current session of current window
        write text "{escaped_cmd}"
    end tell
end tell
'''
    try:
        subprocess.run(["osascript", "-e", script], capture_output=True)
        return True
    except Exception:
        return False


def _launch_macos_warp(command: str, cwd: str | None) -> bool:
    """Launch in Warp terminal."""
    # Warp uses a different protocol
    return False


def _launch_linux_terminal(action: DeepLinkAction) -> bool:
    """Launch on Linux."""
    command = _build_command(action)

    # Try common terminals
    terminals = [
        ("gnome-terminal", ["gnome-terminal", "--", "bash", "-c", command]),
        ("konsole", ["konsole", "-e", "bash", "-c", command]),
        ("xterm", ["xterm", "-e", command]),
        ("alacritty", ["alacritty", "-e", "bash", "-c", command]),
        ("kitty", ["kitty", "bash", "-c", command]),
    ]

    for _name, args in terminals:
        if shutil.which(args[0]):
            try:
                subprocess.Popen(
                    args,
                    cwd=action.cwd,
                    start_new_session=True,
                )
                return True
            except Exception:
                continue

    return False


def _launch_windows_terminal(action: DeepLinkAction) -> bool:
    """Launch on Windows."""
    command = _build_command(action)

    # Try Windows Terminal first, then cmd
    try:
        # Windows Terminal
        if shutil.which("wt.exe"):
            subprocess.Popen(
                ["wt.exe", "cmd", "/k", command],
                cwd=action.cwd,
            )
            return True

        # Fallback to cmd
        subprocess.Popen(
            ["cmd.exe", "/k", command],
            cwd=action.cwd,
        )
        return True

    except Exception:
        return False


def _launch_generic_terminal(command: str, cwd: str | None) -> bool:
    """Launch in a generic terminal emulator."""
    terminal = os.getenv("TERMINAL")

    if terminal and shutil.which(terminal):
        try:
            subprocess.Popen(
                [terminal, "-e", command],
                cwd=cwd,
                start_new_session=True,
            )
            return True
        except Exception:
            pass

    return False
