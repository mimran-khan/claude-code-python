"""
Computer-use feature gates (Chicago / GrowthBook parity + env overrides).

Migrated from: utils/computerUse/gates.ts
"""

from __future__ import annotations

import json
import os
import platform
from dataclasses import dataclass
from typing import Any, Literal

from ..env_utils import is_env_truthy
from .types import CoordinateMode

GateStatus = Literal["passed", "failed", "unknown"]


@dataclass
class ComputerUseGate:
    name: str
    status: GateStatus
    message: str = ""


@dataclass(frozen=True)
class CuSubGates:
    pixelValidation: bool = False
    clipboardPasteMultiline: bool = True
    mouseAnimation: bool = True
    hideBeforeAction: bool = True
    autoTargetDisplay: bool = True
    clipboardGuard: bool = True


_CHICAGO_DEFAULTS: dict[str, Any] = {
    "enabled": False,
    "pixelValidation": False,
    "clipboardPasteMultiline": True,
    "mouseAnimation": True,
    "hideBeforeAction": True,
    "autoTargetDisplay": True,
    "clipboardGuard": True,
    "coordinateMode": "pixels",
}

_frozen_coordinate_mode: CoordinateMode | None = None


def _read_chicago_config() -> dict[str, Any]:
    raw = os.getenv("GROWTHBOOK_TENGU_MALORT_PEDWAY", "")
    partial: dict[str, Any] = {}
    if raw.strip():
        try:
            parsed = json.loads(raw)
            if isinstance(parsed, dict):
                partial = parsed
        except json.JSONDecodeError:
            pass
    return {**_CHICAGO_DEFAULTS, **partial}


def get_subscription_type() -> str:
    return (os.getenv("CLAUDE_SUBSCRIPTION_TIER") or os.getenv("CLAUDE_CODE_SUBSCRIPTION") or "max").lower()


def _has_required_subscription() -> bool:
    if os.getenv("USER_TYPE") == "ant":
        return True
    tier = get_subscription_type()
    return tier in ("max", "pro")


def get_chicago_enabled() -> bool:
    if (
        os.getenv("USER_TYPE") == "ant"
        and os.getenv("MONOREPO_ROOT_DIR")
        and not is_env_truthy(os.getenv("ALLOW_ANT_COMPUTER_USE_MCP"))
    ):
        return False
    return _has_required_subscription() and bool(_read_chicago_config().get("enabled"))


def get_chicago_sub_gates() -> CuSubGates:
    cfg = _read_chicago_config()
    return CuSubGates(
        pixelValidation=bool(cfg.get("pixelValidation", False)),
        clipboardPasteMultiline=bool(cfg.get("clipboardPasteMultiline", True)),
        mouseAnimation=bool(cfg.get("mouseAnimation", True)),
        hideBeforeAction=bool(cfg.get("hideBeforeAction", True)),
        autoTargetDisplay=bool(cfg.get("autoTargetDisplay", True)),
        clipboardGuard=bool(cfg.get("clipboardGuard", True)),
    )


def get_chicago_coordinate_mode() -> CoordinateMode:
    global _frozen_coordinate_mode
    if _frozen_coordinate_mode is None:
        raw = _read_chicago_config().get("coordinateMode", "pixels")
        _frozen_coordinate_mode = raw if raw in ("pixels", "normalized") else "pixels"
    return _frozen_coordinate_mode


def is_computer_use_enabled() -> bool:
    """True if user forced via env or Chicago rollout is on."""
    return is_env_truthy(os.getenv("CLAUDE_CODE_ENABLE_COMPUTER_USE")) or get_chicago_enabled()


def is_computer_use_available() -> bool:
    """Desktop session and feature enabled."""
    if os.getenv("SSH_CLIENT") or os.getenv("SSH_TTY"):
        return False
    sysname = platform.system()
    if sysname not in ("Darwin", "Windows") and not (os.getenv("DISPLAY") or os.getenv("WAYLAND_DISPLAY")):
        return False
    return is_computer_use_enabled()


def check_computer_use_gates() -> list[ComputerUseGate]:
    gates: list[ComputerUseGate] = []
    sysname = platform.system()
    if sysname == "Darwin":
        gates.append(ComputerUseGate(name="platform", status="passed", message="macOS"))
    elif sysname == "Windows":
        gates.append(ComputerUseGate(name="platform", status="passed", message="Windows"))
    else:
        gates.append(ComputerUseGate(name="platform", status="passed", message=sysname))

    if get_chicago_enabled() or is_env_truthy(os.getenv("CLAUDE_CODE_ENABLE_COMPUTER_USE")):
        gates.append(
            ComputerUseGate(name="feature", status="passed", message="Computer use enabled"),
        )
    else:
        gates.append(
            ComputerUseGate(
                name="feature",
                status="failed",
                message="Chicago disabled; set GROWTHBOOK_TENGU_MALORT_PEDWAY or CLAUDE_CODE_ENABLE_COMPUTER_USE",
            ),
        )

    if os.getenv("SSH_CLIENT") or os.getenv("SSH_TTY"):
        gates.append(ComputerUseGate(name="ssh", status="failed", message="SSH session"))
    else:
        gates.append(ComputerUseGate(name="ssh", status="passed", message="Not SSH"))

    display = os.getenv("DISPLAY") or os.getenv("WAYLAND_DISPLAY")
    if sysname == "Darwin" or sysname == "Windows" or display:
        gates.append(ComputerUseGate(name="display", status="passed", message="Display OK"))
    else:
        gates.append(ComputerUseGate(name="display", status="unknown", message="No DISPLAY"))

    return gates


def check_accessibility_permission() -> bool:
    if platform.system() != "Darwin":
        return True
    return True
