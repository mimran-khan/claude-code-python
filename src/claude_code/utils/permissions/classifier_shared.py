"""Shared classifier types (``utils/permissions/classifierShared.ts``)."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Literal

ClassifierLabel = Literal["allow", "deny", "ask", "unknown"]


@dataclass
class ClassifierSignal:
    label: ClassifierLabel
    confidence: float = 0.0
    reason: str | None = None
