"""
Dangerous / gated cmdlet sets (``utils/powershell/dangerousCmdlets.ts``).
"""

from __future__ import annotations

from ..permissions.dangerous_patterns import CROSS_PLATFORM_CODE_EXEC
from .aliases import COMMON_ALIASES

FILEPATH_EXECUTION_CMDLETS: set[str] = {
    "invoke-command",
    "start-job",
    "start-threadjob",
    "register-scheduledjob",
}

DANGEROUS_SCRIPT_BLOCK_CMDLETS: set[str] = {
    "invoke-command",
    "invoke-expression",
    "start-job",
    "start-threadjob",
    "register-scheduledjob",
    "register-engineevent",
    "register-objectevent",
    "register-wmievent",
    "new-pssession",
    "enter-pssession",
}

MODULE_LOADING_CMDLETS: set[str] = {
    "import-module",
    "ipmo",
    "install-module",
    "save-module",
    "update-module",
    "install-script",
    "save-script",
}

SHELLS_AND_SPAWNERS: tuple[str, ...] = (
    "pwsh",
    "powershell",
    "cmd",
    "bash",
    "wsl",
    "sh",
    "start-process",
    "start",
    "add-type",
    "new-object",
)


def _aliases_of(targets: set[str]) -> list[str]:
    tlow = {x.lower() for x in targets}
    return [a for a, t in COMMON_ALIASES.items() if t.lower() in tlow]


NETWORK_CMDLETS: set[str] = {"invoke-webrequest", "invoke-restmethod"}

ALIAS_HIJACK_CMDLETS: set[str] = {
    "set-alias",
    "sal",
    "new-alias",
    "nal",
    "set-variable",
    "sv",
    "new-variable",
    "nv",
}

WMI_CIM_CMDLETS: set[str] = {"invoke-wmimethod", "iwmi", "invoke-cimmethod"}

ARG_GATED_CMDLETS: set[str] = {
    "select-object",
    "sort-object",
    "group-object",
    "where-object",
    "measure-object",
    "write-output",
    "write-host",
    "start-sleep",
    "format-table",
    "format-list",
    "format-wide",
    "format-custom",
    "out-string",
    "out-host",
    "ipconfig",
    "hostname",
    "route",
}


def _never_suggest_core() -> set[str]:
    core: set[str] = set(SHELLS_AND_SPAWNERS)
    core |= FILEPATH_EXECUTION_CMDLETS
    core |= DANGEROUS_SCRIPT_BLOCK_CMDLETS
    core |= MODULE_LOADING_CMDLETS
    core |= NETWORK_CMDLETS
    core |= ALIAS_HIJACK_CMDLETS
    core |= WMI_CIM_CMDLETS
    core |= ARG_GATED_CMDLETS
    core.add("foreach-object")
    for p in CROSS_PLATFORM_CODE_EXEC:
        if " " not in p:
            core.add(p.lower())
    core |= set(_aliases_of(core))
    return core


NEVER_SUGGEST: frozenset[str] = frozenset(_never_suggest_core())
