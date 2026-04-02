"""
Mobile app QR / pairing.

Migrated from: commands/mobile/index.ts
"""

from __future__ import annotations

from claude_code.commands.spec import CommandSpec

from .command import MobileCommand

MOBILE_COMMAND = CommandSpec(
    type="local-jsx",
    name="mobile",
    aliases=("ios", "android"),
    description="Show QR code to download the Claude mobile app",
    load_symbol="claude_code.commands.mobile.ui",
)

__all__ = ["MOBILE_COMMAND", "MobileCommand"]
