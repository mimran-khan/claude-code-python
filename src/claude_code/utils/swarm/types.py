"""Swarm backend types. Migrated from: utils/swarm/backends/types.ts (subset)"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Literal

BackendType = Literal["tmux", "iterm2", "in-process"]
PaneBackendType = Literal["tmux", "iterm2"]
PaneId = str


@dataclass
class CreatePaneResult:
    pane_id: PaneId
    is_first_teammate: bool
