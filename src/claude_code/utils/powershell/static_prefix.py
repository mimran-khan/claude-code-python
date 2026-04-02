"""
Static prefix extraction for permission rules (``utils/powershell/staticPrefix.ts``).

Full ``buildPrefix`` / fig-spec depth rules from TypeScript are not ported; cmdlet
names return as-is, and simple literal external commands return the bare name.
"""

from __future__ import annotations

from .dangerous_cmdlets import NEVER_SUGGEST
from .parser import ParsedCommandElement, parse_powershell_command


async def get_command_prefix_static(command: str) -> dict[str, str | None] | None:
    parsed = await parse_powershell_command(command)
    if not parsed.get("valid"):
        return None
    from .parser import get_all_commands

    cmds = get_all_commands(parsed)
    first = next((c for c in cmds if c.get("elementType") == "CommandAst"), None)
    if not first:
        return {"commandPrefix": None}
    prefix = await _extract_prefix_from_element(first)
    return {"commandPrefix": prefix}


async def _extract_prefix_from_element(cmd: ParsedCommandElement) -> str | None:
    if cmd.get("nameType") == "application":
        return None
    name = cmd.get("name") or ""
    if not name:
        return None
    if name.lower() in NEVER_SUGGEST:
        return None
    if cmd.get("nameType") == "cmdlet":
        return name
    ets = cmd.get("elementTypes") or []
    if not ets or ets[0] != "StringConstant":
        return None
    for i in range(len(cmd.get("args", []))):
        t = ets[i + 1] if i + 1 < len(ets) else None
        if t not in ("StringConstant", "Parameter"):
            return None
    return name


async def get_compound_command_prefixes_static(
    command: str,
    exclude_subcommand: object | None = None,
) -> list[str]:
    parsed = await parse_powershell_command(command)
    if not parsed.get("valid"):
        return []
    from .parser import get_all_commands

    commands = [c for c in get_all_commands(parsed) if c.get("elementType") == "CommandAst"]
    out: list[str] = []
    for c in commands:
        excl = exclude_subcommand
        if excl is not None and callable(excl) and excl(c):
            continue
        p = await _extract_prefix_from_element(c)
        if p:
            out.append(p)
    return out
