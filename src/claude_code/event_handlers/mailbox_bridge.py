"""
Bridge in-process mailbox revision to prompt submit.

Migrated from: hooks/useMailboxBridge.ts
"""

from __future__ import annotations

from collections.abc import Callable
from typing import Protocol


class MailboxLike(Protocol):
    revision: int

    def subscribe(self, fn: Callable[[], None]) -> Callable[[], None]: ...

    def poll(self) -> object | None: ...


def on_mailbox_revision_idle(
    mailbox: MailboxLike,
    *,
    is_loading: bool,
    on_submit_message: Callable[[str], bool],
) -> None:
    if is_loading:
        return
    msg = mailbox.poll()
    if msg is None:
        return
    content = getattr(msg, "content", msg)
    if isinstance(content, str):
        on_submit_message(content)
