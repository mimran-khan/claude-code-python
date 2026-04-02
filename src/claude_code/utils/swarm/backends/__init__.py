"""Swarm pane backends (tmux / iTerm2 / in-process). Skeleton migration."""

from __future__ import annotations

from . import detection, registry
from . import types as backend_types

__all__ = ["backend_types", "detection", "registry"]
