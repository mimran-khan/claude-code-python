"""Tests for ``claude_code.utils.vim`` (placeholder package for TS parity)."""

from __future__ import annotations

import importlib.util
from pathlib import Path


def test_vim_module_exports_empty_all() -> None:
    # Load ``vim/__init__.py`` directly so we do not import ``claude_code.utils`` (heavy deps).
    root = Path(__file__).resolve().parents[3]
    vim_init = root / "src" / "claude_code" / "utils" / "vim" / "__init__.py"
    spec = importlib.util.spec_from_file_location("claude_code.utils.vim._test_target", vim_init)
    assert spec is not None and spec.loader is not None
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    assert mod.__all__ == []
