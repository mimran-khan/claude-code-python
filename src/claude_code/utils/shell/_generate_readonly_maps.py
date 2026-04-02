#!/usr/bin/env python3
"""Generate readonly_maps_generated.py from readOnlyCommandValidation.ts (dev-only)."""

from __future__ import annotations

import re
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
OUT_PATH = HERE / "readonly_maps_generated.py"


def _resolve_ts_path() -> Path:
    for base in HERE.parents:
        cand = base / "utils/shell/readOnlyCommandValidation.ts"
        if cand.is_file():
            return cand
    raise FileNotFoundError("readOnlyCommandValidation.ts not found above shell package")


def strip_line_comments(line: str) -> str:
    if "//" not in line:
        return line
    in_s = False
    quote = ""
    for idx, ch in enumerate(line):
        if in_s:
            if ch == quote and (idx == 0 or line[idx - 1] != "\\"):
                in_s = False
        elif ch in "\"'":
            in_s = True
            quote = ch
        elif ch == "/" and idx + 1 < len(line) and line[idx + 1] == "/":
            return line[:idx].rstrip()
    return line


def read_ts_file() -> str:
    raw = _resolve_ts_path().read_text(encoding="utf-8")
    return "\n".join(strip_line_comments(ln) for ln in raw.splitlines())


def skip_ws(s: str, i: int) -> int:
    while i < len(s) and s[i] in " \t\n\r":
        i += 1
    return i


def read_identifier_key(s: str, i: int) -> tuple[str, int]:
    """TS object key: bare identifier (e.g. ``rg``) or hyphenated."""
    j = i
    while j < len(s) and (s[j].isalnum() or s[j] in "-_"):
        j += 1
    if j == i:
        raise ValueError("expected identifier key")
    return s[i:j], j


def read_object_key(s: str, i: int) -> tuple[str, int]:
    i = skip_ws(s, i)
    if i < len(s) and s[i] in "\"'":
        return read_string(s, i)
    return read_identifier_key(s, i)


def read_string(s: str, i: int) -> tuple[str, int]:
    q = s[i]
    if q not in "\"'":
        raise ValueError(f"expected string at {i}")
    i += 1
    out: list[str] = []
    while i < len(s):
        ch = s[i]
        if ch == "\\":
            i += 1
            if i < len(s):
                out.append(s[i])
                i += 1
            continue
        if ch == q:
            return "".join(out), i + 1
        out.append(ch)
        i += 1
    raise ValueError("unterminated string")


def parse_dict_body(s: str, env: dict[str, dict[str, str]], spread_allowed: bool) -> tuple[dict[str, str], int]:
    result: dict[str, str] = {}
    i = skip_ws(s, 0)
    if i >= len(s) or s[i] != "{":
        raise ValueError("expected {")
    i += 1
    while True:
        i = skip_ws(s, i)
        if i < len(s) and s[i] == "}":
            return result, i + 1
        if spread_allowed and s.startswith("...", i):
            i += 3
            j = i
            while j < len(s) and (s[j].isalnum() or s[j] == "_"):
                j += 1
            name = s[i:j]
            if name not in env:
                raise KeyError(f"unknown spread {name!r}")
            result.update(env[name])
            i = skip_ws(s, j)
            if i < len(s) and s[i] == ",":
                i += 1
            continue
        key, i = read_string(s, i)
        i = skip_ws(s, i)
        if i >= len(s) or s[i] != ":":
            raise ValueError("expected :")
        i += 1
        i = skip_ws(s, i)
        val, i = read_string(s, i)
        result[key] = val
        i = skip_ws(s, i)
        if i < len(s) and s[i] == ",":
            i += 1


def extract_braced_block(s: str, start_open_brace: int) -> tuple[str, int]:
    depth = 0
    for k in range(start_open_brace, len(s)):
        if s[k] == "{":
            depth += 1
        elif s[k] == "}":
            depth -= 1
            if depth == 0:
                return s[start_open_brace + 1 : k], k + 1
    raise ValueError("unbalanced")


def extract_bracket_block(s: str, start_open_bracket: int) -> tuple[str, int]:
    depth = 0
    for k in range(start_open_bracket, len(s)):
        if s[k] == "[":
            depth += 1
        elif s[k] == "]":
            depth -= 1
            if depth == 0:
                return s[start_open_bracket + 1 : k], k + 1
    raise ValueError("unbalanced bracket")


def parse_top_level_consts(text: str) -> dict[str, dict[str, str]]:
    env: dict[str, dict[str, str]] = {}
    for m in re.finditer(
        r"const\s+([A-Z0-9_]+)\s*:\s*Record\s*<\s*string\s*,\s*FlagArgType\s*>\s*=\s*\{",
        text,
    ):
        name = m.group(1)
        start = m.end() - 1
        body, _ = extract_braced_block(text, start)
        d, _ = parse_dict_body("{" + body + "}", env, spread_allowed=False)
        env[name] = d
    return env


def py_repr_dict(d: dict[str, str], indent: str = "    ") -> str:
    lines = ["{"]
    for k in sorted(d.keys(), key=lambda x: (len(x), x)):
        lines.append(f'{indent}{repr(k)}: "{d[k]}",')
    lines.append("}")
    return "\n".join(lines)


def parse_command_map(marker: str, text: str, env: dict[str, dict[str, str]]) -> dict[str, dict[str, str]]:
    i = text.find(marker)
    if i < 0:
        raise ValueError(f"marker missing: {marker!r}")
    j = text.find("{", i)
    body, _ = extract_braced_block(text, j)
    cmds: dict[str, dict[str, str]] = {}
    pos = 0
    while pos < len(body):
        pos = skip_ws(body, pos)
        if pos >= len(body):
            break
        cmd, pos2 = read_object_key(body, pos)
        pos = skip_ws(body, pos2)
        if pos >= len(body) or body[pos] != ":":
            raise ValueError(f"expected : after {cmd!r}")
        pos += 1
        pos = skip_ws(body, pos)
        if pos >= len(body) or body[pos] != "{":
            raise ValueError(f"expected {{ for {cmd!r}")
        inner, pos = extract_braced_block(body, pos)
        pos = skip_ws(body, pos)
        if pos < len(body) and body[pos] == ",":
            pos += 1
        m = re.search(r"safeFlags\s*:\s*\{", inner)
        if not m:
            raise ValueError(f"safeFlags missing {cmd!r}")
        brace_pos = m.end() - 1
        sbody, _ = extract_braced_block(inner, brace_pos)
        flags, _ = parse_dict_body("{" + sbody + "}", env, spread_allowed=True)
        cmds[cmd] = flags
    return cmds


def parse_external_readonly_commands(text: str) -> list[str]:
    m = re.search(r"export const EXTERNAL_READONLY_COMMANDS[^=]*=\s*\[", text)
    if not m:
        raise ValueError("EXTERNAL_READONLY_COMMANDS")
    j = m.end() - 1
    inner, _ = extract_bracket_block(text, j)
    out: list[str] = []
    pos = 0
    while pos < len(inner):
        pos = skip_ws(inner, pos)
        if pos >= len(inner):
            break
        s, pos2 = read_string(inner, pos)
        out.append(s)
        pos = skip_ws(inner, pos2)
        if pos < len(inner) and inner[pos] == ",":
            pos += 1
    return out


def main() -> None:
    text = read_ts_file()
    env = parse_top_level_consts(text)
    git = parse_command_map("export const GIT_READ_ONLY_COMMANDS", text, env)
    gh = parse_command_map("export const GH_READ_ONLY_COMMANDS", text, env)
    docker = parse_command_map("export const DOCKER_READ_ONLY_COMMANDS", text, env)
    rg = parse_command_map("export const RIPGREP_READ_ONLY_COMMANDS", text, env)
    pyright = parse_command_map("export const PYRIGHT_READ_ONLY_COMMANDS", text, env)
    external = parse_external_readonly_commands(text)

    lines = [
        '"""AUTO-GENERATED — run _generate_readonly_maps.py to refresh."""',
        "from __future__ import annotations",
        "",
        "FlagArgType = str",
        "",
    ]
    for name in sorted(env.keys()):
        lines.append(f"{name}: dict[str, FlagArgType] = " + py_repr_dict(env[name]) + "\n")

    def emit_map(py_name: str, data: dict[str, dict[str, str]]) -> None:
        lines.append(f"{py_name}: dict[str, dict[str, FlagArgType]] = {{")
        for cmd in sorted(data.keys()):
            lines.append(f"    {cmd!r}: " + py_repr_dict(data[cmd], indent="        ") + ",")
        lines.append("}")

    emit_map("GIT_READ_ONLY_COMMANDS_SAFE_FLAGS", git)
    emit_map("GH_READ_ONLY_COMMANDS_SAFE_FLAGS", gh)
    emit_map("DOCKER_READ_ONLY_COMMANDS_SAFE_FLAGS", docker)
    emit_map("RIPGREP_READ_ONLY_COMMANDS_SAFE_FLAGS", rg)
    emit_map("PYRIGHT_READ_ONLY_COMMANDS_SAFE_FLAGS", pyright)

    lines.append("EXTERNAL_READONLY_COMMANDS: tuple[str, ...] = (")
    for s in external:
        lines.append(f"    {s!r},")
    lines.append(")")

    OUT_PATH.write_text("\n".join(lines) + "\n", encoding="utf-8")
    print(
        f"Wrote {OUT_PATH} git={len(git)} gh={len(gh)} docker={len(docker)} "
        f"rg={len(rg)} pyright={len(pyright)} ext={len(external)} consts={len(env)}",
        file=sys.stderr,
    )


if __name__ == "__main__":
    main()
