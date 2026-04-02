"""
Fig-spec-driven command prefix depth (shell-agnostic).

Migrated from: utils/shell/specPrefix.ts
"""

from __future__ import annotations

from claude_code.utils.bash.command_spec import Argument, CommandSpec, Option

URL_PROTOCOLS = ("http://", "https://", "ftp://")

DEPTH_RULES: dict[str, int] = {
    "rg": 2,
    "pre-commit": 2,
    "gcloud": 4,
    "gcloud compute": 6,
    "gcloud beta": 6,
    "aws": 4,
    "az": 4,
    "kubectl": 3,
    "docker": 3,
    "dotnet": 3,
    "git push": 2,
}


def _to_args(val: Argument | list[Argument] | None) -> list[Argument]:
    if val is None:
        return []
    return list(val) if isinstance(val, list) else [val]


def _option_names(opt: Option) -> list[str]:
    if isinstance(opt.name, list):
        return list(opt.name)
    return [opt.name]


def _is_known_subcommand(arg: str, spec: CommandSpec | None) -> bool:
    if not spec or not spec.subcommands:
        return False
    low = arg.lower()
    for sub in spec.subcommands:
        if isinstance(sub.name, list):
            if any(n.lower() == low for n in sub.name):
                return True
        elif sub.name.lower() == low:
            return True
    return False


def _flag_takes_arg(flag: str, next_arg: str | None, spec: CommandSpec | None) -> bool:
    if spec and spec.options:
        for opt in spec.options:
            if flag in _option_names(opt):
                return bool(opt.args)
    if spec and spec.subcommands and next_arg and not next_arg.startswith("-"):
        return not _is_known_subcommand(next_arg, spec)
    return False


def _find_first_subcommand(args: list[str], spec: CommandSpec | None) -> str | None:
    i = 0
    while i < len(args):
        arg = args[i]
        if not arg:
            i += 1
            continue
        if arg.startswith("-"):
            if _flag_takes_arg(arg, args[i + 1] if i + 1 < len(args) else None, spec):
                i += 1
            i += 1
            continue
        if not spec or not spec.subcommands:
            return arg
        if _is_known_subcommand(arg, spec):
            return arg
        i += 1
    return None


async def _should_stop_at_arg(arg: str, prior: list[str], spec: CommandSpec | None) -> bool:
    if arg.startswith("-"):
        return True
    dot = arg.rfind(".")
    has_ext = dot > 0 and dot < len(arg) - 1 and ":" not in arg[dot + 1 :]
    has_file = "/" in arg or has_ext
    has_url = any(arg.startswith(p) for p in URL_PROTOCOLS)
    if not has_file and not has_url:
        return False
    if spec and spec.options and prior and prior[-1] == "-m":
        for opt in spec.options:
            if "-m" in _option_names(opt) and opt.args:
                args_list = _to_args(opt.args)
                if any(bool(getattr(a, "is_module", False)) for a in args_list):
                    return False
    return True


async def _calculate_depth(command: str, args: list[str], spec: CommandSpec | None) -> int:
    first_sub = _find_first_subcommand(args, spec)
    cmd_low = command.lower()
    key = f"{cmd_low} {first_sub.lower()}" if first_sub else cmd_low
    if key in DEPTH_RULES:
        return DEPTH_RULES[key]
    if cmd_low in DEPTH_RULES:
        return DEPTH_RULES[cmd_low]
    if not spec:
        return 2

    if spec.options and any(a and a.startswith("-") for a in args):
        for arg in args:
            if not arg or not arg.startswith("-"):
                continue
            for opt in spec.options:
                if arg in _option_names(opt) and opt.args:
                    al = _to_args(opt.args)
                    if any(getattr(a, "is_command", False) or getattr(a, "is_module", False) for a in al):
                        return 3

    if first_sub and spec.subcommands:
        fsl = first_sub.lower()
        subcommand = None
        for sub in spec.subcommands:
            if isinstance(sub.name, list):
                if any(n.lower() == fsl for n in sub.name):
                    subcommand = sub
                    break
            elif sub.name.lower() == fsl:
                subcommand = sub
                break
        if subcommand:
            if subcommand.args:
                sa = _to_args(subcommand.args)
                if any(getattr(a, "is_command", False) for a in sa):
                    return 3
                if any(getattr(a, "is_variadic", False) for a in sa):
                    return 2
            if subcommand.subcommands:
                return 4
            if not subcommand.args:
                return 2
            return 3

    if spec.args:
        aa = _to_args(spec.args)
        if any(getattr(a, "is_command", False) for a in aa):
            if not isinstance(spec.args, list) and getattr(spec.args, "is_command", False):
                return 2
            idx = next((i for i, a in enumerate(aa) if getattr(a, "is_command", False)), 0)
            return min(2 + idx, 3)
        if not spec.subcommands:
            if any(getattr(a, "is_variadic", False) for a in aa):
                return 1
            if aa and not getattr(aa[0], "is_optional", False):
                return 2

    if spec.args:
        aa = _to_args(spec.args)
        if any(getattr(a, "is_dangerous", False) for a in aa):
            return 3
    return 2


async def build_prefix(command: str, args: list[str], spec: CommandSpec | None) -> str:
    max_depth = await _calculate_depth(command, args, spec)
    parts = [command]
    has_subcommands = bool(spec and spec.subcommands)
    found_sub = False
    i = 0
    while i < len(args):
        arg = args[i]
        if not arg or len(parts) >= max_depth:
            break
        if arg.startswith("-"):
            if arg == "-c" and command.lower() in ("python", "python3"):
                break
            if spec and spec.options:
                for opt in spec.options:
                    if arg in _option_names(opt) and opt.args:
                        al = _to_args(opt.args)
                        if any(getattr(a, "is_command", False) or getattr(a, "is_module", False) for a in al):
                            parts.append(arg)
                            break
                else:
                    if has_subcommands and not found_sub:
                        if _flag_takes_arg(arg, args[i + 1] if i + 1 < len(args) else None, spec):
                            i += 1
                        i += 1
                        continue
                    break
            else:
                if has_subcommands and not found_sub:
                    if _flag_takes_arg(arg, args[i + 1] if i + 1 < len(args) else None, spec):
                        i += 1
                    i += 1
                    continue
                break
            i += 1
            continue
        if await _should_stop_at_arg(arg, args[:i], spec):
            break
        if has_subcommands and not found_sub:
            found_sub = _is_known_subcommand(arg, spec)
        parts.append(arg)
        i += 1
    return " ".join(parts)


__all__ = ["DEPTH_RULES", "build_prefix"]
