"""Transport protocol for CLI SDK streaming."""

from __future__ import annotations

from collections.abc import Callable
from typing import Any, Protocol

StdoutMessage = dict[str, Any]


class Transport(Protocol):
    """Bidirectional transport for SDK print / remote mode."""

    async def connect(self) -> None:
        """Open the transport (WebSocket connect or start SSE reader)."""
        ...

    async def write(self, message: StdoutMessage) -> None:
        """Send one outbound message."""
        ...

    def close(self) -> None:
        """Close connections and stop background work."""
        ...

    def set_on_data(self, callback: Callable[[str], None]) -> None:
        """Receive inbound NDJSON chunks (may contain multiple lines)."""
        ...

    def set_on_close(self, callback: Callable[..., None]) -> None:
        """Connection lost or permanent close."""
        ...
