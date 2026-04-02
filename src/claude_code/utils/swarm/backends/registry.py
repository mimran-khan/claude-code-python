"""Backend registry. Migrated from: utils/swarm/backends/registry.ts"""

from __future__ import annotations

from typing import Any

_registry: dict[str, Any] = {}


def register_backend(name: str, backend: Any) -> None:
    _registry[name] = backend


def get_backend(name: str) -> Any | None:
    return _registry.get(name)
