"""Well-known PowerShell common parameters.

Migrated from: tools/PowerShellTool/commonParameters.ts (subset).
"""

COMMON_PARAMETERS = frozenset(
    {
        "verbose",
        "debug",
        "erroraction",
        "warningaction",
        "informationaction",
        "errorvariable",
        "warningvariable",
        "informationvariable",
        "outvariable",
        "outbuffer",
        "pipelinevariable",
        "confirm",
        "whatif",
    },
)


def is_common_parameter(name: str) -> bool:
    return name.lstrip("-").lower().replace("-", "") in {p.replace("-", "") for p in COMMON_PARAMETERS}
