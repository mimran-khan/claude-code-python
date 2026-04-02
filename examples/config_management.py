#!/usr/bin/env python3
"""
Read and update Claude Code global configuration safely.

**Important:** This example points ``CLAUDE_CONFIG_DIR`` at a temporary directory
so it never overwrites your real ``~/.claude`` settings. Set ``CLAUDE_CONFIG_DIR``
yourself only if you intend to work with a real config tree.

Run:
  python examples/config_management.py
"""

from __future__ import annotations

import os
import sys
import tempfile
from dataclasses import replace

# Configure an isolated config home *before* importing claude_code config helpers
# (``get_claude_config_home_dir`` is cached per process).
_ISOLATED_ROOT = tempfile.mkdtemp(prefix="claude-code-example-config-")
os.environ["CLAUDE_CONFIG_DIR"] = _ISOLATED_ROOT

from _path_setup import ensure_src_on_path

ensure_src_on_path()

from claude_code.config import (
    get_config_path,
    get_global_config,
    get_project_config,
    set_global_config,
)
from claude_code.config.types import ProjectConfig


def main() -> int:
    print(f"Using isolated CLAUDE_CONFIG_DIR={_ISOLATED_ROOT!r}\n")

    try:
        path = get_config_path()
        print(f"Resolved config path: {path}")

        cfg = get_global_config()
        print(f"Default theme: {cfg.theme!r}, verbose_mode={cfg.verbose_mode}")

        fake_project = os.path.normpath(os.path.abspath(os.getcwd()))
        projects = dict(cfg.projects)
        projects[fake_project] = ProjectConfig(
            allowed_tools=["Read", "Glob"],
            has_trust_dialog_accepted=True,
        )

        updated = replace(
            cfg,
            theme="dark",
            verbose_mode=True,
            projects=projects,
        )

        set_global_config(updated)
        round_trip = get_global_config()

        if round_trip.theme != "dark" or not round_trip.verbose_mode:
            print("Round-trip config mismatch after write.", file=sys.stderr)
            return 1

        proj = get_project_config(fake_project)
        print(f"Project config for {fake_project}:")
        print(f"  allowed_tools: {proj.allowed_tools}")

        print("\nConfig write/read cycle completed successfully.")
        print("Remove the temp directory when finished if you ran this manually.")

    except OSError as exc:
        print(f"Config I/O error: {exc}", file=sys.stderr)
        return 1
    except Exception as exc:
        print(f"Unexpected error: {exc}", file=sys.stderr)
        return 1

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
