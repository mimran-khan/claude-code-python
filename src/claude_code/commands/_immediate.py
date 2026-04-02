"""Inference config immediate flag (ported from utils/immediateCommand.ts)."""

from __future__ import annotations

import os


def should_inference_config_command_be_immediate() -> bool:
    return os.environ.get("CLAUDE_CODE_IMMEDIATE_INFERENCE_CMD", "1") != "0"
