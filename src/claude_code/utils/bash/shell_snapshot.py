"""
Shell environment snapshots (bash/zsh) for provider integration.

Migrated from: ``utils/bash/ShellSnapshot.ts`` (createAndSaveSnapshot and helpers).
"""

from __future__ import annotations

import asyncio
import os
import random
import string
import subprocess
import time
from pathlib import Path

from claude_code.utils.bash.shell_quote import quote
from claude_code.utils.cleanup_registry import register_cleanup
from claude_code.utils.cwd import get_cwd
from claude_code.utils.debug import log_for_debugging
from claude_code.utils.env_utils import get_claude_config_home_dir
from claude_code.utils.file import path_exists
from claude_code.utils.log import log_error
from claude_code.utils.platform import get_platform
from claude_code.utils.ripgrep import get_ripgrep_config
from claude_code.utils.subprocess_env import subprocess_env

SNAPSHOT_CREATION_TIMEOUT_SEC = 10.0


def _get_config_file(shell_path: str) -> str:
    if "zsh" in shell_path:
        name = ".zshrc"
    elif "bash" in shell_path:
        name = ".bashrc"
    else:
        name = ".profile"
    return str(Path.home() / name)


def _create_ripgrep_alias_target() -> str:
    """Shell word(s) for ``alias rg=…`` when system rg is missing."""
    cfg = get_ripgrep_config()
    quoted_path = quote([cfg.command])
    if cfg.args:
        quoted_args = " ".join(quote([a]) for a in cfg.args)
        return f"{quoted_path} {quoted_args}"
    return quoted_path


def _get_user_snapshot_content(config_file: str) -> str:
    is_zsh = config_file.endswith(".zshrc")
    if is_zsh:
        func_block = """
      echo "# Functions" >> "$SNAPSHOT_FILE"

      typeset -f > /dev/null 2>&1

      typeset +f | grep -vE '^_[^_]' | while read func; do
        typeset -f "$func" >> "$SNAPSHOT_FILE"
      done
    """
        opt_block = """
      echo "# Shell Options" >> "$SNAPSHOT_FILE"
      setopt | sed 's/^/setopt /' | head -n 1000 >> "$SNAPSHOT_FILE"
    """
    else:
        func_block = """
      echo "# Functions" >> "$SNAPSHOT_FILE"

      declare -f > /dev/null 2>&1

      declare -F | cut -d' ' -f3 | grep -vE '^_[^_]' | while read func; do
        encoded_func=$(declare -f "$func" | base64 )
        echo "eval `$(echo '$encoded_func' | base64 -d)`" > /dev/null 2>&1" >> "$SNAPSHOT_FILE"
      done
    """
        opt_block = """
      echo "# Shell Options" >> "$SNAPSHOT_FILE"
      shopt -p | head -n 1000 >> "$SNAPSHOT_FILE"
      set -o | grep "on" | awk '{print "set -o " $1}' | head -n 1000 >> "$SNAPSHOT_FILE"
      echo "shopt -s expand_aliases" >> "$SNAPSHOT_FILE"
    """

    alias_block = """
      echo "# Aliases" >> "$SNAPSHOT_FILE"
      if [[ "$OSTYPE" == "msys" ]] || [[ "$OSTYPE" == "cygwin" ]]; then
        alias | grep -v "='winpty " | sed 's/^alias //g' | sed 's/^/alias -- /' \\
          | head -n 1000 >> "$SNAPSHOT_FILE"
      else
        alias | sed 's/^alias //g' | sed 's/^/alias -- /' \\
          | head -n 1000 >> "$SNAPSHOT_FILE"
      fi
  """
    return func_block + opt_block + alias_block


async def _get_claude_code_snapshot_content() -> str:
    path_value = os.environ.get("PATH", "")
    if get_platform() == "windows":
        try:
            proc = await asyncio.create_subprocess_shell(
                "echo $PATH",
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.DEVNULL,
            )
            out, _ = await asyncio.wait_for(proc.communicate(), timeout=5.0)
            if proc.returncode == 0 and out:
                path_value = out.decode("utf-8", errors="replace").strip()
        except (TimeoutError, OSError):
            pass

    rg_alias_target = _create_ripgrep_alias_target()
    escaped = rg_alias_target.replace("'", "'\\''")
    content = """
      # Check for rg availability
      echo "# Check for rg availability" >> "$SNAPSHOT_FILE"
      echo "if ! (unalias rg 2>/dev/null; command -v rg) >/dev/null 2>&1; then" >> "$SNAPSHOT_FILE"
  """
    content += f"""
      echo '  alias rg='"'{escaped}'" >> "$SNAPSHOT_FILE"
    """
    content += """
      echo "fi" >> "$SNAPSHOT_FILE"
  """
    qpath = quote([path_value or ""])
    content += f"""

      # Add PATH to the file
      echo "export PATH={qpath}" >> "$SNAPSHOT_FILE"
  """
    return content


async def _get_snapshot_script_async(
    shell_path: str,
    snapshot_file_path: str,
    config_file_exists: bool,
) -> str:
    config_file = _get_config_file(shell_path)
    is_zsh = config_file.endswith(".zshrc")
    if config_file_exists:
        user_content = _get_user_snapshot_content(config_file)
    elif not is_zsh:
        user_content = 'echo "shopt -s expand_aliases" >> "$SNAPSHOT_FILE"'
    else:
        user_content = ""

    claude_content = await _get_claude_code_snapshot_content()
    q_snap = quote([snapshot_file_path])
    cfg_line = f'source "{config_file}" < /dev/null' if config_file_exists else "# No user config file to source"
    return f"""SNAPSHOT_FILE={q_snap}
      {cfg_line}

      echo "# Snapshot file" >| "$SNAPSHOT_FILE"

      echo "# Unset all aliases to avoid conflicts with functions" >> "$SNAPSHOT_FILE"
      echo "unalias -a 2>/dev/null || true" >> "$SNAPSHOT_FILE"

      {user_content}

      {claude_content}

      if [ ! -f "$SNAPSHOT_FILE" ]; then
        echo "Error: Snapshot file was not created at $SNAPSHOT_FILE" >&2
        exit 1
      fi
    """


def _random_id() -> str:
    return "".join(random.choices(string.ascii_lowercase + string.digits, k=6))


async def create_and_save_snapshot(bin_shell: str) -> str | None:
    """
    Create a shell snapshot file mirroring the user's rc, or return ``None`` on failure.

    TS: ``createAndSaveSnapshot(binShell: string)``.
    """
    shell_type = "zsh" if "zsh" in bin_shell else "bash" if "bash" in bin_shell else "sh"
    log_for_debugging(f"Creating shell snapshot for {shell_type} ({bin_shell})")

    config_file = _get_config_file(bin_shell)
    log_for_debugging(f"Looking for shell config file: {config_file}")
    config_exists = path_exists(config_file)
    if not config_exists:
        log_for_debugging(
            f"Shell config file not found: {config_file}, creating snapshot with defaults only",
        )

    snapshots_dir = Path(get_claude_config_home_dir()) / "shell-snapshots"
    ts_ms = int(time.time() * 1000)
    snapshot_path = snapshots_dir / f"snapshot-{shell_type}-{ts_ms}-{_random_id()}.sh"

    try:
        snapshots_dir.mkdir(parents=True, exist_ok=True)
    except OSError as exc:
        log_for_debugging(f"Could not create snapshots dir: {exc}")
        return None

    try:
        snapshot_script = await _get_snapshot_script_async(
            bin_shell,
            str(snapshot_path),
            config_exists,
        )
    except Exception as exc:
        log_for_debugging(f"Failed to build snapshot script: {exc}")
        log_error(exc)
        return None

    log_for_debugging(f"Creating snapshot at: {snapshot_path}")

    if os.environ.get("CLAUDE_CODE_DONT_INHERIT_ENV"):
        env: dict[str, str] = {}
    else:
        env = dict(subprocess_env())
    env.update(
        {
            "SHELL": bin_shell,
            "GIT_EDITOR": "true",
            "CLAUDECODE": "1",
        },
    )

    def _run() -> subprocess.CompletedProcess[str]:
        return subprocess.run(
            [bin_shell, "-c", "-l", snapshot_script],
            env=env,
            cwd=get_cwd(),
            capture_output=True,
            text=True,
            timeout=SNAPSHOT_CREATION_TIMEOUT_SEC,
        )

    try:
        result = await asyncio.to_thread(_run)
    except subprocess.TimeoutExpired:
        log_for_debugging("Shell snapshot creation timed out")
        return None
    except Exception as exc:
        log_for_debugging(f"Unexpected error during snapshot creation: {exc}")
        log_error(exc)
        return None

    if result.returncode != 0:
        log_for_debugging(
            f"Shell snapshot creation failed: rc={result.returncode} stderr={result.stderr!r}",
        )
        log_error(
            RuntimeError(f"Failed to create shell snapshot: {result.stderr or result.stdout}"),
        )
        return None

    if not snapshot_path.is_file():
        log_for_debugging("Shell snapshot file not found after creation")
        return None

    log_for_debugging(f"Shell snapshot created successfully ({snapshot_path.stat().st_size} bytes)")

    snap_str = str(snapshot_path)

    async def _cleanup() -> None:
        try:
            Path(snap_str).unlink(missing_ok=True)
            log_for_debugging(f"Cleaned up session snapshot: {snap_str}")
        except OSError as exc:
            log_for_debugging(f"Error cleaning up session snapshot: {exc}")

    register_cleanup(_cleanup)
    return snap_str


__all__ = ["create_and_save_snapshot"]
