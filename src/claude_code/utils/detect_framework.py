"""
Heuristic project framework detection.

The TypeScript tree does not include ``utils/detectFramework.ts`` in this snapshot;
this module provides minimal parity for Python callers.
"""

from __future__ import annotations

import json
import os
from dataclasses import dataclass
from enum import StrEnum
from typing import Any


class FrameworkKind(StrEnum):
    UNKNOWN = "unknown"
    NODE = "node"
    PYTHON = "python"
    RUST = "rust"
    GO = "go"


@dataclass
class DetectedFramework:
    kind: FrameworkKind
    details: dict[str, Any]


def detect_framework(cwd: str | None = None) -> DetectedFramework:
    root = cwd or os.getcwd()
    pkg = os.path.join(root, "package.json")
    if os.path.isfile(pkg):
        try:
            with open(pkg, encoding="utf-8") as f:
                data = json.load(f)
            return DetectedFramework(FrameworkKind.NODE, {"package_json": bool(data)})
        except Exception:
            return DetectedFramework(FrameworkKind.NODE, {"package_json": False})
    if os.path.isfile(os.path.join(root, "pyproject.toml")) or os.path.isfile(os.path.join(root, "setup.py")):
        return DetectedFramework(FrameworkKind.PYTHON, {})
    if os.path.isfile(os.path.join(root, "Cargo.toml")):
        return DetectedFramework(FrameworkKind.RUST, {})
    if os.path.isfile(os.path.join(root, "go.mod")):
        return DetectedFramework(FrameworkKind.GO, {})
    return DetectedFramework(FrameworkKind.UNKNOWN, {})
