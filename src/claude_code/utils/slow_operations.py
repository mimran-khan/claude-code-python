"""
Slow JSON / clone / sync write instrumentation.

Migrated from: utils/slowOperations.ts (without Bun ``feature()`` DCE — uses env gates).
"""

from __future__ import annotations

import json
import os
import time
import traceback
from collections.abc import Iterator
from contextlib import contextmanager, suppress
from copy import deepcopy
from typing import Any, TypeVar

from ..bootstrap.state import add_slow_operation
from .debug import log_for_debugging

T = TypeVar("T")


def _threshold_ms() -> float:
    raw = os.environ.get("CLAUDE_CODE_SLOW_OPERATION_THRESHOLD_MS")
    if raw is not None:
        try:
            v = float(raw)
            if v >= 0 and v == v:
                return v
        except ValueError:
            pass
    if os.environ.get("NODE_ENV") == "development":
        return 20.0
    if os.environ.get("USER_TYPE") == "ant":
        return 300.0
    return float("inf")


SLOW_OPERATION_THRESHOLD_MS = _threshold_ms()

_is_logging = False


def caller_frame(stack: str | None) -> str:
    if not stack:
        return ""
    for line in stack.split("\n"):
        if "slow_operations" in line:
            continue
        parts = line.strip().split()
        if parts:
            return f" @ {parts[-1]}"
    return ""


def _describe_value(v: Any) -> str:
    if isinstance(v, list):
        return f"Array[{len(v)}]"
    if isinstance(v, dict):
        return f"Object{{{len(v)} keys}}"
    if isinstance(v, str):
        return v if len(v) <= 80 else f"{v[:80]}…"
    return str(v)


def _build_description(template: str, values: tuple[Any, ...]) -> str:
    if not values:
        return template
    parts = template.split("%s", len(values))
    out = parts[0]
    for i, val in enumerate(values):
        out += _describe_value(val)
        if i + 1 < len(parts):
            out += parts[i + 1]
    return out


@contextmanager
def slow_logging(template: str, *values: Any) -> Iterator[None]:
    """Time a block; log when duration exceeds threshold (ANT / dev builds)."""
    global _is_logging
    if float("inf") == SLOW_OPERATION_THRESHOLD_MS:
        yield
        return
    start = time.perf_counter()
    try:
        yield
    finally:
        duration_ms = (time.perf_counter() - start) * 1000
        if duration_ms > SLOW_OPERATION_THRESHOLD_MS and not _is_logging:
            _is_logging = True
            try:
                desc = _build_description(template, values)
                stack = caller_frame("".join(traceback.format_stack(limit=12)))
                msg = f"[SLOW OPERATION DETECTED] {desc}{stack} ({duration_ms:.1f}ms)"
                log_for_debugging(msg)
                add_slow_operation(desc + stack, int(duration_ms))
            finally:
                _is_logging = False


def json_stringify(value: Any, **kwargs: Any) -> str:
    with slow_logging("JSON.stringify(%s)", value):
        return json.dumps(value, **kwargs)


def json_parse(text: str, **kwargs: Any) -> Any:
    with slow_logging("JSON.parse(%s)", text):
        return json.loads(text, **kwargs)


def clone(value: T) -> T:
    with slow_logging("deepcopy(%s)", value):
        return deepcopy(value)


def clone_deep(value: T) -> T:
    with slow_logging("deepcopy(%s)", value):
        return deepcopy(value)


def write_file_sync_deprecated(
    file_path: str,
    data: str | bytes,
    *,
    encoding: str = "utf-8",
    flush: bool = False,
) -> None:
    """Sync write with optional fsync (legacy). Prefer async IO."""
    with slow_logging("write_file_sync(%s, …)", file_path):
        if isinstance(data, str):
            with open(file_path, "w", encoding=encoding) as f:
                f.write(data)
                if flush:
                    f.flush()
                    os.fsync(f.fileno())
        else:
            with open(file_path, "wb") as f:
                f.write(data)
                if flush:
                    f.flush()
                    os.fsync(f.fileno())
        with suppress(OSError):
            os.chmod(file_path, 0o600)
