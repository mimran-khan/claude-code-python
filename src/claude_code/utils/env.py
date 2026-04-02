"""
Environment detection utilities.

Functions for detecting environment, IDE, terminal, and runtime.

Migrated from: utils/env.ts (348 lines)
"""

from __future__ import annotations

import os
import shutil
from functools import cache
from pathlib import Path
from typing import Literal

from dotenv import load_dotenv

from .env_utils import get_claude_config_home_dir, get_env_or_default, is_env_truthy

Platform = Literal["win32", "darwin", "linux"]


JETBRAINS_IDES = [
    "pycharm",
    "intellij",
    "webstorm",
    "phpstorm",
    "rubymine",
    "clion",
    "goland",
    "rider",
    "datagrip",
    "appcode",
    "dataspell",
    "aqua",
    "gateway",
    "fleet",
    "jetbrains",
    "androidstudio",
]


@cache
def get_global_claude_file() -> str:
    """Get the path to the global Claude config file."""
    config_dir = get_claude_config_home_dir()

    # Legacy fallback
    legacy_path = os.path.join(config_dir, ".config.json")
    if os.path.exists(legacy_path):
        return legacy_path

    # Default location
    return os.path.join(
        os.getenv("CLAUDE_CONFIG_DIR") or os.path.expanduser("~"),
        ".claude.json",
    )


@cache
def has_internet_access() -> bool:
    """Check if internet access is available."""
    try:
        import socket

        with socket.create_connection(("1.1.1.1", 53), timeout=1):
            return True
    except OSError:
        return False


def is_command_available(command: str) -> bool:
    """Check if a command is available in PATH."""
    return shutil.which(command) is not None


@cache
def detect_package_managers() -> list[str]:
    """Detect available package managers."""
    managers = []
    for pm in ["npm", "yarn", "pnpm"]:
        if is_command_available(pm):
            managers.append(pm)
    return managers


@cache
def detect_runtimes() -> list[str]:
    """Detect available JavaScript runtimes."""
    runtimes = []
    for rt in ["bun", "deno", "node"]:
        if is_command_available(rt):
            runtimes.append(rt)
    return runtimes


@cache
def is_wsl_environment() -> bool:
    """Check if running in WSL environment."""
    try:
        return os.path.exists("/proc/sys/fs/binfmt_misc/WSLInterop")
    except Exception:
        return False


def is_conductor() -> bool:
    """Check if running via Conductor."""
    return os.getenv("__CFBundleIdentifier") == "com.conductor.app"


def detect_terminal() -> str | None:
    """Detect the terminal type."""
    # Check for Cursor
    if os.getenv("CURSOR_TRACE_ID"):
        return "cursor"

    askpass = os.getenv("VSCODE_GIT_ASKPASS_MAIN", "")
    if "cursor" in askpass.lower():
        return "cursor"
    if "windsurf" in askpass.lower():
        return "windsurf"
    if "antigravity" in askpass.lower():
        return "antigravity"

    bundle_id = (os.getenv("__CFBundleIdentifier") or "").lower()
    if "vscodium" in bundle_id:
        return "codium"
    if "windsurf" in bundle_id:
        return "windsurf"
    if "android.studio" in bundle_id:
        return "androidstudio"

    # Check for JetBrains IDEs
    for ide in JETBRAINS_IDES:
        if ide in bundle_id:
            return ide

    terminal_program = os.getenv("TERM_PROGRAM", "")

    if terminal_program == "vscode":
        return "vscode"
    if terminal_program == "iTerm.app":
        return "iterm"
    if terminal_program == "Apple_Terminal":
        return "terminal"
    if terminal_program == "tmux":
        return "tmux"

    if os.getenv("KITTY_WINDOW_ID"):
        return "kitty"
    if os.getenv("ALACRITTY_SOCKET"):
        return "alacritty"
    if os.getenv("WEZTERM_PANE"):
        return "wezterm"

    return None


def detect_editor_from_env() -> str | None:
    """Detect the editor from environment variables."""
    return os.getenv("VISUAL") or os.getenv("EDITOR")


@cache
def get_platform() -> Platform:
    """Get the current platform."""
    import platform

    system = platform.system().lower()

    if system == "darwin":
        return "darwin"
    if system == "windows":
        return "win32"
    return "linux"


def is_darwin() -> bool:
    """Check if running on macOS."""
    return get_platform() == "darwin"


def is_windows() -> bool:
    """Check if running on Windows."""
    return get_platform() == "win32"


def is_linux() -> bool:
    """Check if running on Linux."""
    return get_platform() == "linux"


def get_shell() -> str:
    """Get the current shell."""
    return os.getenv("SHELL") or "/bin/sh"


def is_interactive_shell() -> bool:
    """Check if running in an interactive shell."""
    import sys

    return sys.stdin.isatty() and sys.stdout.isatty()


def get_home_dir() -> str:
    """Get the home directory."""
    return os.path.expanduser("~")


def get_username() -> str:
    """Get the current username."""
    import getpass

    return getpass.getuser()


@cache
def get_hostname() -> str:
    """Get the hostname."""
    import socket

    return socket.gethostname()


def is_ci_environment() -> bool:
    """Check if running in a CI environment."""
    ci_vars = ["CI", "CONTINUOUS_INTEGRATION", "GITHUB_ACTIONS", "GITLAB_CI", "JENKINS_URL"]
    return any(is_env_truthy(os.getenv(var)) for var in ci_vars)


def is_docker() -> bool:
    """Check if running in Docker."""
    return os.path.exists("/.dockerenv") or os.path.exists("/run/.containerenv")


def get_terminal_columns() -> int:
    """Get the terminal width in columns."""
    try:
        import shutil

        return shutil.get_terminal_size().columns
    except Exception:
        return 80


def get_terminal_rows() -> int:
    """Get the terminal height in rows."""
    try:
        import shutil

        return shutil.get_terminal_size().lines
    except Exception:
        return 24


def find_dotenv_file(
    start_dir: str | None = None,
    filename: str = ".env",
) -> str | None:
    """
    Walk upward from ``start_dir`` (or cwd) and return the first existing dotenv path.
    """
    from .cwd import get_cwd

    root = Path(start_dir or get_cwd()).resolve()
    for directory in [root, *root.parents]:
        candidate = directory / filename
        try:
            if candidate.is_file():
                return str(candidate)
        except OSError:
            continue
    return None


def load_dotenv_file(
    path: str | Path,
    *,
    override: bool = False,
) -> bool:
    """
    Load a single ``.env`` (or other env file) into ``os.environ``.

    Returns True if the file existed and was passed to python-dotenv.
    """
    p = Path(path)
    if not p.is_file():
        return False
    load_dotenv(dotenv_path=p, override=override)
    return True


def load_dotenv_for_project(
    start_dir: str | None = None,
    *,
    filenames: tuple[str, ...] = (".env", ".env.local"),
    override: bool = False,
) -> list[str]:
    """
    Load dotenv files from the project directory chain (closest match per name).

    For each filename, walks upward from ``start_dir`` and loads the closest match.
    Returns paths that were loaded.
    """
    loaded: list[str] = []
    for name in filenames:
        found = find_dotenv_file(start_dir, name)
        if found and found not in loaded and load_dotenv_file(found, override=override):
            loaded.append(found)
    return loaded


def merge_env_with_defaults(
    values: dict[str, str],
    defaults: dict[str, str],
) -> dict[str, str]:
    """Merge parsed env values onto defaults (explicit values win)."""
    return {**defaults, **values}


def getenv_with_default(key: str, default: str = "") -> str:
    """
    Read ``os.environ`` with a default; same as :func:`env_utils.get_env_or_default`.
    """
    return get_env_or_default(key, default)
