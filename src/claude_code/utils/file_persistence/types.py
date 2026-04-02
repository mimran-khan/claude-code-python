"""Dataclasses for file persistence events."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Literal

TurnStartTime = float

EnvironmentKind = Literal["byoc", "anthropic_cloud"]


@dataclass
class PersistedFile:
    filename: str
    file_id: str


@dataclass
class FailedPersistence:
    filename: str
    error: str


@dataclass
class FilesPersistedEventData:
    files: list[PersistedFile]
    failed: list[FailedPersistence]
