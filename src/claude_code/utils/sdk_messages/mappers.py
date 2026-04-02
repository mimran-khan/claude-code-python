"""
SDK message wire-format mappers (stubs until full TS parity).

These functions exist so imports succeed; behavior is identity or minimal coercion.
"""

from __future__ import annotations

from typing import Any


def from_sdk_compact_metadata(obj: Any) -> Any:
    return obj


def local_command_output_to_sdk_assistant_message(obj: Any) -> Any:
    return obj


def to_internal_messages(obj: Any) -> Any:
    return obj


def to_sdk_compact_metadata(obj: Any) -> Any:
    return obj


def to_sdk_messages(obj: Any) -> Any:
    return obj


def to_sdk_rate_limit_info(obj: Any) -> Any:
    return obj
