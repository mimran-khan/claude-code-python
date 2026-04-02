"""Unicode figures and symbols for UI display."""

import sys

# Platform detection
_is_darwin = sys.platform == "darwin"

# The former is better vertically aligned, but isn't usually supported on Windows/Linux
BLACK_CIRCLE = "⏺" if _is_darwin else "●"
BULLET_OPERATOR = "∙"
TEARDROP_ASTERISK = "✻"
UP_ARROW = "\u2191"  # ↑ - used for opus 1m merge notice
DOWN_ARROW = "\u2193"  # ↓ - used for scroll hint
LIGHTNING_BOLT = "↯"  # \u21af - used for fast mode indicator
EFFORT_LOW = "○"  # \u25cb - effort level: low
EFFORT_MEDIUM = "◐"  # \u25d0 - effort level: medium
EFFORT_HIGH = "●"  # \u25cf - effort level: high
EFFORT_MAX = "◉"  # \u25c9 - effort level: max (Opus 4.6 only)

# Media/trigger status indicators
PLAY_ICON = "\u25b6"  # ▶
PAUSE_ICON = "\u23f8"  # ⏸

# MCP subscription indicators
REFRESH_ARROW = "\u21bb"  # ↻ - used for resource update indicator
CHANNEL_ARROW = "\u2190"  # ← - inbound channel message indicator
INJECTED_ARROW = "\u2192"  # → - cross-session injected message indicator
FORK_GLYPH = "\u2442"  # ⑂ - fork directive indicator

# Review status indicators (ultrareview diamond states)
DIAMOND_OPEN = "\u25c7"  # ◇ - running
DIAMOND_FILLED = "\u25c6"  # ◆ - completed/failed
REFERENCE_MARK = "\u203b"  # ※ - komejirushi, away-summary recap marker

# Issue flag indicator
FLAG_ICON = "\u2691"  # ⚑ - used for issue flag banner

# Blockquote indicator
BLOCKQUOTE_BAR = "\u258e"  # ▎ - left one-quarter block, used as blockquote line prefix
HEAVY_HORIZONTAL = "\u2501"  # ━ - heavy box-drawing horizontal

# Bridge status indicators
BRIDGE_SPINNER_FRAMES = [
    "\u00b7|\u00b7",
    "\u00b7/\u00b7",
    "\u00b7\u2014\u00b7",
    "\u00b7\\\u00b7",
]
BRIDGE_READY_INDICATOR = "\u00b7\u2714\ufe0e\u00b7"
BRIDGE_FAILED_INDICATOR = "\u00d7"
