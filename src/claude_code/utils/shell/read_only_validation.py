"""
Read-only shell command validation maps and flag parsing.

Migrated from: utils/shell/readOnlyCommandValidation.ts

Safe-flag data is generated into :mod:`readonly_maps_generated`; callbacks are defined here.
"""

from __future__ import annotations

import re
from collections.abc import Callable
from dataclasses import dataclass
from typing import Literal

from claude_code.utils.platform import get_platform

from .readonly_maps_generated import (
    DOCKER_READ_ONLY_COMMANDS_SAFE_FLAGS,
    EXTERNAL_READONLY_COMMANDS,
    GH_READ_ONLY_COMMANDS_SAFE_FLAGS,
    GIT_READ_ONLY_COMMANDS_SAFE_FLAGS,
    PYRIGHT_READ_ONLY_COMMANDS_SAFE_FLAGS,
    RIPGREP_READ_ONLY_COMMANDS_SAFE_FLAGS,
)

FlagArgType = Literal["none", "number", "string", "char", "{}", "EOF"]

DangerCb = Callable[[str, list[str]], bool]


@dataclass
class ExternalCommandConfig:
    safe_flags: dict[str, str]
    additional_command_is_dangerous_callback: DangerCb | None = None
    respects_double_dash: bool | None = True


# --- git / gh callbacks (ported from TS) ---


def _git_reflog_dangerous(_raw: str, args: list[str]) -> bool:
    dangerous = frozenset({"expire", "delete", "exists"})
    for token in args:
        if not token or token.startswith("-"):
            continue
        return token in dangerous
    return False


def _git_remote_show_dangerous(_raw: str, args: list[str]) -> bool:
    positional = [a for a in args if a != "-n"]
    if len(positional) != 1:
        return True
    return not re.match(r"^[a-zA-Z0-9_-]+$", positional[0])


def _git_remote_dangerous(_raw: str, args: list[str]) -> bool:
    return any(a not in ("-v", "--verbose") for a in args)


def _git_tag_dangerous(_raw: str, args: list[str]) -> bool:
    flags_with_args = frozenset(
        {
            "--contains",
            "--no-contains",
            "--merged",
            "--no-merged",
            "--points-at",
            "--sort",
            "--format",
            "-n",
        }
    )
    i = 0
    seen_list = False
    seen_dd = False
    while i < len(args):
        token = args[i]
        if not token:
            i += 1
            continue
        if token == "--" and not seen_dd:
            seen_dd = True
            i += 1
            continue
        if not seen_dd and token.startswith("-"):
            if token in ("--list", "-l") or (
                not token.startswith("--") and len(token) > 2 and "=" not in token and "l" in token[1:]
            ):
                seen_list = True
            if "=" in token:
                i += 1
            elif token in flags_with_args:
                i += 2
            else:
                i += 1
        else:
            if not seen_list:
                return True
            i += 1
    return False


def _git_branch_dangerous(_raw: str, args: list[str]) -> bool:
    flags_with_args = frozenset(
        {
            "--contains",
            "--no-contains",
            "--points-at",
            "--sort",
        }
    )
    flags_optional = frozenset({"--merged", "--no-merged"})
    i = 0
    last_flag = ""
    seen_list = False
    seen_dd = False
    while i < len(args):
        token = args[i]
        if not token:
            i += 1
            continue
        if token == "--" and not seen_dd:
            seen_dd = True
            last_flag = ""
            i += 1
            continue
        if not seen_dd and token.startswith("-"):
            if token in ("--list", "-l") or (
                token.startswith("-")
                and not token.startswith("--")
                and len(token) > 2
                and "=" not in token
                and "l" in token[1:]
            ):
                seen_list = True
            if "=" in token:
                last_flag = token.split("=", maxsplit=1)[0] or ""
                i += 1
            elif token in flags_with_args:
                last_flag = token
                i += 2
            else:
                last_flag = token
                i += 1
        else:
            if not seen_list and last_flag not in flags_optional:
                return True
            i += 1
    return False


def _pyright_dangerous(_raw: str, args: list[str]) -> bool:
    return any(t in ("--watch", "-w") for t in args)


def _gh_dangerous(_raw: str, args: list[str]) -> bool:
    for token in args:
        if not token:
            continue
        value = token
        if token.startswith("-"):
            eq = token.find("=")
            if eq == -1:
                continue
            value = token[eq + 1 :]
            if not value:
                continue
        if "/" not in value and "://" not in value and "@" not in value:
            continue
        if "://" in value:
            return True
        if "@" in value:
            return True
        if value.count("/") >= 2:
            return True
    return False


def _build_git_commands() -> dict[str, ExternalCommandConfig]:
    out: dict[str, ExternalCommandConfig] = {}
    for cmd, flags in GIT_READ_ONLY_COMMANDS_SAFE_FLAGS.items():
        sf = dict(flags)
        cb: DangerCb | None = None
        if cmd == "git reflog":
            cb = _git_reflog_dangerous
        elif cmd == "git remote show":
            cb = _git_remote_show_dangerous
        elif cmd == "git remote":
            cb = _git_remote_dangerous
        elif cmd == "git tag":
            cb = _git_tag_dangerous
        elif cmd == "git branch":
            cb = _git_branch_dangerous
        out[cmd] = ExternalCommandConfig(safe_flags=sf, additional_command_is_dangerous_callback=cb)
    return out


def _build_gh_commands() -> dict[str, ExternalCommandConfig]:
    out: dict[str, ExternalCommandConfig] = {}
    for cmd, flags in GH_READ_ONLY_COMMANDS_SAFE_FLAGS.items():
        out[cmd] = ExternalCommandConfig(
            safe_flags=dict(flags),
            additional_command_is_dangerous_callback=_gh_dangerous,
        )
    return out


def _build_simple_map(raw: dict[str, dict[str, str]]) -> dict[str, ExternalCommandConfig]:
    return {k: ExternalCommandConfig(safe_flags=dict(v)) for k, v in raw.items()}


GIT_READ_ONLY_COMMANDS: dict[str, ExternalCommandConfig] = _build_git_commands()
GH_READ_ONLY_COMMANDS: dict[str, ExternalCommandConfig] = _build_gh_commands()
DOCKER_READ_ONLY_COMMANDS: dict[str, ExternalCommandConfig] = _build_simple_map(
    DOCKER_READ_ONLY_COMMANDS_SAFE_FLAGS,
)
RIPGREP_READ_ONLY_COMMANDS: dict[str, ExternalCommandConfig] = _build_simple_map(
    RIPGREP_READ_ONLY_COMMANDS_SAFE_FLAGS,
)

_PYRIGHT_FLAGS = dict(PYRIGHT_READ_ONLY_COMMANDS_SAFE_FLAGS["pyright"])
PYRIGHT_READ_ONLY_COMMANDS: dict[str, ExternalCommandConfig] = {
    "pyright": ExternalCommandConfig(
        safe_flags=_PYRIGHT_FLAGS,
        respects_double_dash=False,
        additional_command_is_dangerous_callback=_pyright_dangerous,
    ),
}

FLAG_PATTERN = re.compile(r"^-[a-zA-Z0-9_-]")


def validate_flag_argument(value: str, arg_type: str) -> bool:
    if arg_type == "none":
        return False
    if arg_type == "number":
        return bool(re.fullmatch(r"\d+", value))
    if arg_type == "string":
        return True
    if arg_type == "char":
        return len(value) == 1
    if arg_type == "{}":
        return value == "{}"
    if arg_type == "EOF":
        return value == "EOF"
    return False


def contains_vulnerable_unc_path(path_or_command: str) -> bool:
    if get_platform() != "windows":
        return False
    if re.search(r"\\\\[^\s\\/]+(?:@(?:\d+|ssl))?(?:[\\/]|$|\s)", path_or_command, re.I):
        return True
    if re.search(r"(?<!:)\/\/[^\s\\/]+(?:@(?:\d+|ssl))?(?:[\\/]|$|\s)", path_or_command, re.I):
        return True
    if re.search(r"/\\{2,}[^\s\\/]", path_or_command):
        return True
    if re.search(r"\\{2,}/[^\s\\/]", path_or_command):
        return True
    if re.search(r"@SSL@\d+", path_or_command, re.I) or re.search(r"@\d+@SSL", path_or_command, re.I):
        return True
    if re.search(r"DavWWWRoot", path_or_command, re.I):
        return True
    if re.search(r"^\\\\(\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3})[\\/]", path_or_command) or re.search(
        r"^\/\/(\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3})[\\/]",
        path_or_command,
    ):
        return True
    return bool(
        re.search(r"^\\\\(\[[\da-fA-F:]+\])[\\/]", path_or_command)
        or re.search(r"^\/\/(\[[\da-fA-F:]+\])[\\/]", path_or_command)
    )


def validate_flags(
    tokens: list[str],
    start_index: int,
    config: ExternalCommandConfig,
    options: dict[str, object] | None = None,
) -> bool:
    """Walk flag tokens; mirrors TS ``validateFlags`` (security-sensitive)."""
    opts = options or {}
    command_name = opts.get("commandName")
    xargs_targets = opts.get("xargsTargetCommands")
    i = start_index
    respects_dd = True if config.respects_double_dash is None else config.respects_double_dash

    while i < len(tokens):
        token = tokens[i]
        if not token:
            i += 1
            continue

        if xargs_targets and command_name == "xargs" and (not token.startswith("-") or token == "--"):
            if token == "--" and i + 1 < len(tokens):
                i += 1
                token = tokens[i]
            if token and token in xargs_targets:
                break
            return False

        if token == "--":
            if respects_dd:
                i += 1
                break
            i += 1
            continue

        if len(token) > 1 and token.startswith("-") and FLAG_PATTERN.match(token):
            has_equals = "=" in token
            flag, *value_parts = token.split("=", 1)
            inline_value = value_parts[0] if value_parts else ""
            if not flag:
                return False
            flag_arg_type = config.safe_flags.get(flag)

            if flag_arg_type is None:
                if command_name == "git" and re.match(r"^-\d+$", flag):
                    i += 1
                    continue
                if command_name in ("grep", "rg") and flag.startswith("-") and not flag.startswith("--"):
                    if len(flag) > 2:
                        potential_flag = flag[:2]
                        potential_value = flag[2:]
                        ft = config.safe_flags.get(potential_flag)
                        if ft is not None and re.fullmatch(r"\d+", potential_value):
                            if ft in ("number", "string") and validate_flag_argument(potential_value, ft):
                                i += 1
                                continue
                            return False
                if flag.startswith("-") and not flag.startswith("--") and len(flag) > 2:
                    for j in range(1, len(flag)):
                        single = "-" + flag[j]
                        ft = config.safe_flags.get(single)
                        if not ft:
                            return False
                        if ft != "none":
                            return False
                    i += 1
                    continue
                return False

            if flag_arg_type == "none":
                if has_equals:
                    return False
                i += 1
            else:
                if has_equals:
                    arg_value = inline_value
                    i += 1
                else:
                    if i + 1 >= len(tokens):
                        return False
                    nxt = tokens[i + 1]
                    if nxt and nxt.startswith("-") and len(nxt) > 1 and FLAG_PATTERN.match(nxt):
                        return False
                    arg_value = tokens[i + 1] or ""
                    i += 2

                if (
                    flag_arg_type == "string"
                    and arg_value.startswith("-")
                    and not (flag == "--sort" and command_name == "git" and re.match(r"^-[a-zA-Z]", arg_value))
                ):
                    return False
                if not validate_flag_argument(arg_value, flag_arg_type):
                    return False
        else:
            i += 1

    return True


__all__ = [
    "DOCKER_READ_ONLY_COMMANDS",
    "EXTERNAL_READONLY_COMMANDS",
    "ExternalCommandConfig",
    "FLAG_PATTERN",
    "FlagArgType",
    "GH_READ_ONLY_COMMANDS",
    "GIT_READ_ONLY_COMMANDS",
    "PYRIGHT_READ_ONLY_COMMANDS",
    "RIPGREP_READ_ONLY_COMMANDS",
    "contains_vulnerable_unc_path",
    "validate_flag_argument",
    "validate_flags",
]
