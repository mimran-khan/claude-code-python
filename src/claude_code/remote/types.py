"""
Remote Session Types.

Type definitions for remote session handling.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Literal

RemoteSessionState = Literal["ready", "connected", "reconnecting", "failed"]


@dataclass
class RemoteSession:
    """A remote session connection."""

    session_id: str = ""
    environment_id: str = ""
    session_url: str = ""
    state: RemoteSessionState = "ready"

    # Connection details
    base_url: str = ""
    org_uuid: str = ""
    model: str = ""

    # Project info
    project_dir: str = ""
    branch: str | None = None
    git_repo_url: str | None = None

    # Metadata
    worker_type: str | None = None
    name: str | None = None
