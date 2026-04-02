"""
Prevent OS idle sleep during long work (macOS caffeinate).

Migrated from: services/preventSleep.ts
"""

from __future__ import annotations

import contextlib
import platform
import subprocess
import threading
from typing import Any

_ref_count = 0
_process: Any | None = None
_timer: threading.Timer | None = None

CAFFEINATE_TIMEOUT_S = 300
RESTART_INTERVAL_S = 4 * 60


def _spawn_caffeinate() -> None:
    global _process
    if platform.system() != "Darwin":
        return
    try:
        _process = subprocess.Popen(
            ["caffeinate", "-dimsu", "-t", str(CAFFEINATE_TIMEOUT_S)],
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
        )
    except OSError:
        _process = None


def _stop_caffeinate() -> None:
    global _process
    if _process is not None:
        try:
            _process.terminate()
            _process.wait(timeout=5)
        except Exception:
            with contextlib.suppress(Exception):
                _process.kill()
        _process = None


def _restart_loop() -> None:
    global _timer
    if _ref_count <= 0:
        return
    _stop_caffeinate()
    _spawn_caffeinate()
    _timer = threading.Timer(RESTART_INTERVAL_S, _restart_loop)
    _timer.daemon = True
    _timer.start()


def start_prevent_sleep() -> None:
    global _ref_count, _timer
    _ref_count += 1
    if _ref_count == 1:
        _spawn_caffeinate()
        _timer = threading.Timer(RESTART_INTERVAL_S, _restart_loop)
        _timer.daemon = True
        _timer.start()


def stop_prevent_sleep() -> None:
    global _ref_count, _timer
    if _ref_count > 0:
        _ref_count -= 1
    if _ref_count == 0:
        if _timer:
            _timer.cancel()
            _timer = None
        _stop_caffeinate()
