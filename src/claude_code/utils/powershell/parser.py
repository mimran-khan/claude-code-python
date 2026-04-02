"""
PowerShell AST parsing via ``pwsh`` and ``parse_body.ps1`` (``utils/powershell/parser.ts``).
"""

from __future__ import annotations

import asyncio
import base64
import json
import os
import re
import shutil
import sys
from pathlib import Path
from typing import Any, Literal, TypedDict, cast

from ..debug import log_for_debugging
from .aliases import COMMON_ALIASES

_PIPELINE_ELEMENT = Literal["CommandAst", "CommandExpressionAst", "ParenExpressionAst"]
_COMMAND_ELEMENT = Literal[
    "ScriptBlock",
    "SubExpression",
    "ExpandableString",
    "MemberInvocation",
    "Variable",
    "StringConstant",
    "Parameter",
    "Other",
]


class ParsedRedirection(TypedDict):
    operator: str
    target: str
    isMerging: bool


class CommandElementChild(TypedDict):
    type: _COMMAND_ELEMENT
    text: str


class ParsedCommandElement(TypedDict, total=False):
    name: str
    nameType: Literal["cmdlet", "application", "unknown"]
    elementType: _PIPELINE_ELEMENT
    args: list[str]
    text: str
    elementTypes: list[_COMMAND_ELEMENT]
    children: list[list[CommandElementChild] | None]
    redirections: list[ParsedRedirection]


class ParsedStatement(TypedDict, total=False):
    statementType: str
    commands: list[ParsedCommandElement]
    redirections: list[ParsedRedirection]
    text: str
    nestedCommands: list[ParsedCommandElement]
    securityPatterns: dict[str, bool]


class ParseError(TypedDict):
    message: str
    errorId: str


class ParsedVariable(TypedDict):
    path: str
    isSplatted: bool


class ParsedPowerShellCommand(TypedDict, total=False):
    valid: bool
    errors: list[ParseError]
    statements: list[ParsedStatement]
    variables: list[ParsedVariable]
    hasStopParsing: bool
    originalCommand: str
    typeLiterals: list[str]
    hasUsingStatements: bool
    hasScriptRequirements: bool


_PS_SCRIPT_PATH = Path(__file__).with_name("parse_body.ps1")
_PARSE_BODY = _PS_SCRIPT_PATH.read_text(encoding="utf-8")
_WINDOWS_ARGV_CAP = 32767
_FIXED_OVERHEAD = 200
_WRAPPER_LEN = len("$EncodedCommand = ''\n")
_SAFETY = 100
_SCRIPT_BUDGET = ((_WINDOWS_ARGV_CAP - _FIXED_OVERHEAD) * 3) // 8
_CMD_B64_BUDGET = _SCRIPT_BUDGET - len(_PARSE_BODY) - _WRAPPER_LEN
WINDOWS_MAX_COMMAND_LENGTH = max(0, int((_CMD_B64_BUDGET * 3) // 4) - _SAFETY)
UNIX_MAX_COMMAND_LENGTH = 4500
MAX_COMMAND_LENGTH = WINDOWS_MAX_COMMAND_LENGTH if sys.platform == "win32" else UNIX_MAX_COMMAND_LENGTH

PS_TOKENIZER_DASH_CHARS: frozenset[str] = frozenset({"-", "\u2013", "\u2014", "\u2015"})
DIRECTORY_CHANGE_CMDLETS: frozenset[str] = frozenset({"set-location", "push-location", "pop-location"})
DIRECTORY_CHANGE_ALIASES: frozenset[str] = frozenset({"cd", "sl", "chdir", "pushd", "popd"})


def _get_parse_timeout_ms() -> int:
    raw = os.environ.get("CLAUDE_CODE_PWSH_PARSE_TIMEOUT_MS", "")
    if raw.isdigit() and int(raw) > 0:
        return int(raw)
    return 5000


def _to_utf16le_base64(text: str) -> str:
    data = text.encode("utf-16-le")
    return base64.b64encode(data).decode("ascii")


def _build_parse_script(command: str) -> str:
    enc = base64.b64encode(command.encode("utf-8")).decode("ascii")
    return f"$EncodedCommand = '{enc}'\n{_PARSE_BODY}"


def get_cached_powershell_path() -> str | None:
    for name in ("pwsh", "powershell"):
        p = shutil.which(name)
        if p:
            return p
    return None


def _ensure_array(value: Any) -> list[Any]:
    if value is None:
        return []
    return value if isinstance(value, list) else [value]


def map_statement_type(raw: str) -> str:
    known = {
        "PipelineAst",
        "PipelineChainAst",
        "AssignmentStatementAst",
        "IfStatementAst",
        "ForStatementAst",
        "ForEachStatementAst",
        "WhileStatementAst",
        "DoWhileStatementAst",
        "DoUntilStatementAst",
        "SwitchStatementAst",
        "TryStatementAst",
        "TrapStatementAst",
        "FunctionDefinitionAst",
        "DataStatementAst",
    }
    return raw if raw in known else "UnknownStatementAst"


def map_element_type(raw: str, expression_type: str | None = None) -> _COMMAND_ELEMENT:
    if raw in ("ScriptBlockExpressionAst",):
        return "ScriptBlock"
    if raw in ("SubExpressionAst", "ArrayExpressionAst", "ParenExpressionAst"):
        return "SubExpression"
    if raw in ("ExpandableStringExpressionAst",):
        return "ExpandableString"
    if raw in ("InvokeMemberExpressionAst", "MemberExpressionAst"):
        return "MemberInvocation"
    if raw in ("VariableExpressionAst",):
        return "Variable"
    if raw in ("StringConstantExpressionAst", "ConstantExpressionAst"):
        return "StringConstant"
    if raw in ("CommandParameterAst",):
        return "Parameter"
    if raw == "CommandExpressionAst" and expression_type:
        return map_element_type(expression_type)
    return "Other"


def classify_command_name(name: str) -> Literal["cmdlet", "application", "unknown"]:
    if re.match(r"^[A-Za-z]+-[A-Za-z][A-Za-z0-9_]*$", name):
        return "cmdlet"
    if re.search(r"[./\\]", name):
        return "application"
    return "unknown"


def strip_module_prefix(name: str) -> str:
    idx = name.rfind("\\")
    if idx < 0:
        return name
    if re.match(r"^[A-Za-z]:", name) or name.startswith("\\\\") or name.startswith(".\\") or name.startswith("..\\"):
        return name
    return name[idx + 1 :]


def transform_redirection(raw: dict[str, Any]) -> ParsedRedirection:
    if raw.get("type") == "MergingRedirectionAst":
        return {"operator": "2>&1", "target": "", "isMerging": True}
    append = bool(raw.get("append"))
    from_stream = str(raw.get("fromStream") or "Output")
    if append:
        op = {"Error": "2>>", "All": "*>>"}.get(from_stream, ">>")
    else:
        op = {"Error": "2>", "All": "*>"}.get(from_stream, ">")
    return {"operator": op, "target": str(raw.get("locationText") or ""), "isMerging": False}


def transform_command_ast(raw: dict[str, Any]) -> ParsedCommandElement:
    cmd_elements = _ensure_array(raw.get("commandElements"))
    name = ""
    args: list[str] = []
    element_types: list[_COMMAND_ELEMENT] = []
    children: list[list[CommandElementChild] | None] = []
    has_children = False
    name_type: Literal["cmdlet", "application", "unknown"] = "unknown"

    if cmd_elements:
        first = cast(dict[str, Any], cmd_elements[0])
        is_first_str = first.get("type") in (
            "StringConstantExpressionAst",
            "ExpandableStringExpressionAst",
        )
        raw_name_unstripped = (
            str(first.get("value"))
            if is_first_str and isinstance(first.get("value"), str)
            else str(first.get("text", ""))
        )
        raw_name = re.sub(r"^['\"]|['\"]$", "", raw_name_unstripped)
        name_type = "application" if re.search(r"[\u0080-\uFFFF]", raw_name) else classify_command_name(raw_name)
        name = strip_module_prefix(raw_name)
        element_types.append(map_element_type(str(first.get("type")), first.get("expressionType")))

        for i in range(1, len(cmd_elements)):
            ce = cast(dict[str, Any], cmd_elements[i])
            is_str = ce.get("type") in (
                "StringConstantExpressionAst",
                "ExpandableStringExpressionAst",
            )
            val = ce.get("value")
            args.append(str(val) if is_str and val is not None else str(ce.get("text", "")))
            element_types.append(map_element_type(str(ce.get("type")), ce.get("expressionType")))
            raw_ch = _ensure_array(ce.get("children"))
            if raw_ch:
                has_children = True
                mapped: list[CommandElementChild] = []
                for c in raw_ch:
                    c = cast(dict[str, Any], c)
                    mapped.append(
                        {
                            "type": map_element_type(str(c.get("type"))),
                            "text": str(c.get("text", "")),
                        }
                    )
                children.append(mapped)
            else:
                children.append(None)

    result: ParsedCommandElement = {
        "name": name,
        "nameType": name_type,
        "elementType": "CommandAst",
        "args": args,
        "text": str(raw.get("text", "")),
        "elementTypes": element_types,
    }
    if has_children:
        result["children"] = children
    redirs = _ensure_array(raw.get("redirections"))
    if redirs:
        result["redirections"] = [transform_redirection(cast(dict[str, Any], r)) for r in redirs]
    return result


def transform_expression_element(raw: dict[str, Any]) -> ParsedCommandElement:
    et: _PIPELINE_ELEMENT = "ParenExpressionAst" if raw.get("type") == "ParenExpressionAst" else "CommandExpressionAst"
    etype = map_element_type(str(raw.get("type")), raw.get("expressionType"))
    return {
        "name": str(raw.get("text", "")),
        "nameType": "unknown",
        "elementType": et,
        "args": [],
        "text": str(raw.get("text", "")),
        "elementTypes": [etype],
    }


def transform_statement(raw: dict[str, Any]) -> ParsedStatement:
    stype = map_statement_type(str(raw.get("type", "")))
    commands: list[ParsedCommandElement] = []
    redirections: list[ParsedRedirection] = []
    elements = _ensure_array(raw.get("elements"))

    if elements:
        for elem in elements:
            e = cast(dict[str, Any], elem)
            if e.get("type") == "CommandAst":
                commands.append(transform_command_ast(e))
                for r in _ensure_array(e.get("redirections")):
                    redirections.append(transform_redirection(cast(dict[str, Any], r)))
            else:
                commands.append(transform_expression_element(e))
                for r in _ensure_array(e.get("redirections")):
                    redirections.append(transform_redirection(cast(dict[str, Any], r)))
        seen = {f"{r['operator']}\0{r['target']}" for r in redirections}
        for r in _ensure_array(raw.get("redirections")):
            pr = transform_redirection(cast(dict[str, Any], r))
            key = f"{pr['operator']}\0{pr['target']}"
            if key not in seen:
                seen.add(key)
                redirections.append(pr)
    else:
        commands.append(
            {
                "name": str(raw.get("text", "")),
                "nameType": "unknown",
                "elementType": "CommandExpressionAst",
                "args": [],
                "text": str(raw.get("text", "")),
            }
        )
        for r in _ensure_array(raw.get("redirections")):
            redirections.append(transform_redirection(cast(dict[str, Any], r)))

    out: ParsedStatement = {
        "statementType": stype,
        "commands": commands,
        "redirections": redirections,
        "text": str(raw.get("text", "")),
    }
    nested = _ensure_array(raw.get("nestedCommands"))
    if nested:
        out["nestedCommands"] = [transform_command_ast(cast(dict[str, Any], x)) for x in nested]
    sp = raw.get("securityPatterns")
    if isinstance(sp, dict):
        out["securityPatterns"] = {k: bool(v) for k, v in sp.items()}
    return out


def _transform_raw_output(raw: dict[str, Any]) -> ParsedPowerShellCommand:
    out: ParsedPowerShellCommand = {
        "valid": bool(raw.get("valid")),
        "errors": [cast(ParseError, e) for e in _ensure_array(raw.get("errors"))],
        "statements": [transform_statement(cast(dict[str, Any], s)) for s in _ensure_array(raw.get("statements"))],
        "variables": [cast(ParsedVariable, v) for v in _ensure_array(raw.get("variables"))],
        "hasStopParsing": bool(raw.get("hasStopParsing")),
        "originalCommand": str(raw.get("originalCommand", "")),
    }
    tl = _ensure_array(raw.get("typeLiterals"))
    if tl:
        out["typeLiterals"] = [str(x) for x in tl]
    if raw.get("hasUsingStatements"):
        out["hasUsingStatements"] = True
    if raw.get("hasScriptRequirements"):
        out["hasScriptRequirements"] = True
    return out


def _invalid(command: str, message: str, error_id: str) -> ParsedPowerShellCommand:
    return {
        "valid": False,
        "errors": [{"message": message, "errorId": error_id}],
        "statements": [],
        "variables": [],
        "hasStopParsing": False,
        "originalCommand": command,
    }


async def _run_pwsh_once(pwsh: str, encoded_script: str, timeout_ms: int) -> tuple[int, str, str, bool]:
    args = ["-NoProfile", "-NonInteractive", "-NoLogo", "-EncodedCommand", encoded_script]
    proc = await asyncio.create_subprocess_exec(
        pwsh,
        *args,
        stdout=asyncio.subprocess.PIPE,
        stderr=asyncio.subprocess.PIPE,
    )
    timed_out = False
    try:
        out_b, err_b = await asyncio.wait_for(proc.communicate(), timeout=timeout_ms / 1000.0)
    except TimeoutError:
        timed_out = True
        proc.kill()
        out_b, err_b = await proc.communicate()
    code = proc.returncode if proc.returncode is not None else 1
    return code, out_b.decode(errors="replace"), err_b.decode(errors="replace"), timed_out


async def parse_powershell_command_impl(command: str) -> ParsedPowerShellCommand:
    if len(command.encode("utf-8")) > MAX_COMMAND_LENGTH:
        return _invalid(
            command,
            f"Command too long ({len(command.encode('utf-8'))} bytes). Max {MAX_COMMAND_LENGTH}.",
            "CommandTooLong",
        )
    pwsh = get_cached_powershell_path()
    if not pwsh:
        return _invalid(command, "PowerShell is not available", "NoPowerShell")

    script = _build_parse_script(command)
    enc_script = _to_utf16le_base64(script)
    timeout = _get_parse_timeout_ms()
    stderr = ""
    code = 1
    timed_out = False
    stdout = ""
    for attempt in range(2):
        code, stdout, stderr, timed_out = await _run_pwsh_once(pwsh, enc_script, timeout)
        if not timed_out:
            break
        log_for_debugging(f"PowerShell parser: pwsh timed out (attempt {attempt + 1})")

    if timed_out:
        return _invalid(command, f"pwsh timed out after {timeout}ms (2 attempts)", "PwshTimeout")
    if code != 0:
        log_for_debugging(f"PowerShell parser: exit {code} stderr={stderr!r}")
        return _invalid(command, f"pwsh exited with code {code}: {stderr}", "PwshError")

    trimmed = stdout.strip()
    if not trimmed:
        return _invalid(command, "No output from PowerShell parser", "EmptyOutput")
    try:
        raw = json.loads(trimmed)
    except json.JSONDecodeError:
        log_for_debugging(f"PowerShell parser: invalid JSON {trimmed[:200]!r}")
        return _invalid(command, "Invalid JSON from PowerShell parser", "InvalidJson")
    return _transform_raw_output(cast(dict[str, Any], raw))


async def parse_powershell_command(command: str) -> ParsedPowerShellCommand:
    return await parse_powershell_command_impl(command)


def get_all_command_names(parsed: ParsedPowerShellCommand) -> list[str]:
    names: list[str] = []
    for stmt in parsed.get("statements", []):
        for cmd in stmt.get("commands", []):
            names.append(cmd.get("name", "").lower())
        for cmd in stmt.get("nestedCommands") or []:
            names.append(cmd.get("name", "").lower())
    return names


def get_all_commands(parsed: ParsedPowerShellCommand) -> list[ParsedCommandElement]:
    cmds: list[ParsedCommandElement] = []
    for stmt in parsed.get("statements", []):
        cmds.extend(stmt.get("commands", []))
        cmds.extend(stmt.get("nestedCommands") or [])
    return cmds


def get_all_redirections(parsed: ParsedPowerShellCommand) -> list[ParsedRedirection]:
    redirs: list[ParsedRedirection] = []
    for stmt in parsed.get("statements", []):
        redirs.extend(stmt.get("redirections", []))
        for cmd in stmt.get("nestedCommands") or []:
            redirs.extend(cmd.get("redirections") or [])
    return redirs


def has_command_named(parsed: ParsedPowerShellCommand, name: str) -> bool:
    lower = name.lower()
    canon_alias = COMMON_ALIASES.get(lower, "")
    canon_lower = canon_alias.lower() if canon_alias else None
    for cmd_name in get_all_command_names(parsed):
        if cmd_name == lower:
            return True
        c = COMMON_ALIASES.get(cmd_name, "")
        if c.lower() == lower:
            return True
        if canon_lower and cmd_name == canon_lower:
            return True
        c2 = COMMON_ALIASES.get(cmd_name, "")
        if canon_lower and c2.lower() == canon_lower:
            return True
    return False


def has_directory_change(parsed: ParsedPowerShellCommand) -> bool:
    return any(n in DIRECTORY_CHANGE_CMDLETS or n in DIRECTORY_CHANGE_ALIASES for n in get_all_command_names(parsed))


def is_single_command(parsed: ParsedPowerShellCommand) -> bool:
    stmts = parsed.get("statements", [])
    if len(stmts) != 1:
        return False
    st = stmts[0]
    if len(st.get("commands", [])) != 1:
        return False
    return not st.get("nestedCommands")


def command_has_arg(command: ParsedCommandElement, arg: str) -> bool:
    la = arg.lower()
    return any(a.lower() == la for a in command.get("args", []))
