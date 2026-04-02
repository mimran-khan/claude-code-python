"""
XDG Base Directory helpers (migrated from ``utils/xdg.ts``).

See https://specifications.freedesktop.org/basedir-spec/latest/
"""

from __future__ import annotations

import os
from collections.abc import Mapping
from pathlib import Path


def _home(env: Mapping[str, str], homedir: str | None) -> Path:
    if homedir is not None:
        return Path(homedir)
    h = env.get("HOME")
    if h:
        return Path(h)
    return Path.home()


def get_xdg_state_home(
    env: Mapping[str, str] | None = None,
    homedir: str | None = None,
) -> str:
    e: Mapping[str, str] = env if env is not None else os.environ
    h = _home(e, homedir)
    return e.get("XDG_STATE_HOME") or str(h / ".local" / "state")


def get_xdg_cache_home(
    env: Mapping[str, str] | None = None,
    homedir: str | None = None,
) -> str:
    e: Mapping[str, str] = env if env is not None else os.environ
    h = _home(e, homedir)
    return e.get("XDG_CACHE_HOME") or str(h / ".cache")


def get_xdg_data_home(
    env: Mapping[str, str] | None = None,
    homedir: str | None = None,
) -> str:
    e: Mapping[str, str] = env if env is not None else os.environ
    h = _home(e, homedir)
    return e.get("XDG_DATA_HOME") or str(h / ".local" / "share")


def get_user_bin_dir(
    env: Mapping[str, str] | None = None,
    homedir: str | None = None,
) -> str:
    h = _home(env if env is not None else os.environ, homedir)
    return str(h / ".local" / "bin")


__all__ = [
    "get_xdg_cache_home",
    "get_xdg_data_home",
    "get_xdg_state_home",
    "get_user_bin_dir",
]
