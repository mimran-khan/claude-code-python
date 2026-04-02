"""Built-in ``pyright`` command spec. Migrated from: utils/bash/specs/pyright.ts"""

from __future__ import annotations

from ..command_spec import Argument, CommandSpec, Option

PYRIGHT_SPEC = CommandSpec(
    name="pyright",
    description="Type checker for Python",
    options=[
        Option(name=["--help", "-h"], description="Show help message"),
        Option(name="--version", description="Print pyright version and exit"),
        Option(
            name=["--watch", "-w"],
            description="Continue to run and watch for changes",
        ),
        Option(
            name=["--project", "-p"],
            description="Use the configuration file at this location",
            args=Argument(name="FILE OR DIRECTORY"),
        ),
        Option(name="-", description="Read file or directory list from stdin"),
        Option(
            name="--createstub",
            description="Create type stub file(s) for import",
            args=Argument(name="IMPORT"),
        ),
        Option(
            name=["--typeshedpath", "-t"],
            description="Use typeshed type stubs at this location",
            args=Argument(name="DIRECTORY"),
        ),
        Option(
            name="--verifytypes",
            description="Verify completeness of types in py.typed package",
            args=Argument(name="IMPORT"),
        ),
        Option(
            name="--ignoreexternal",
            description="Ignore external imports for --verifytypes",
        ),
        Option(
            name="--pythonpath",
            description="Path to the Python interpreter",
            args=Argument(name="FILE"),
        ),
        Option(
            name="--pythonplatform",
            description="Analyze for platform",
            args=Argument(name="PLATFORM"),
        ),
        Option(
            name="--pythonversion",
            description="Analyze for Python version",
            args=Argument(name="VERSION"),
        ),
        Option(
            name=["--venvpath", "-v"],
            description="Directory that contains virtual environments",
            args=Argument(name="DIRECTORY"),
        ),
        Option(name="--outputjson", description="Output results in JSON format"),
        Option(name="--verbose", description="Emit verbose diagnostics"),
        Option(name="--stats", description="Print detailed performance stats"),
        Option(
            name="--dependencies",
            description="Emit import dependency information",
        ),
        Option(
            name="--level",
            description="Minimum diagnostic level",
            args=Argument(name="LEVEL"),
        ),
        Option(
            name="--skipunannotated",
            description="Skip type analysis of unannotated functions",
        ),
        Option(
            name="--warnings",
            description="Use exit code of 1 if warnings are reported",
        ),
        Option(
            name="--threads",
            description="Use up to N threads to parallelize type checking",
            args=Argument(name="N", is_optional=True),
        ),
    ],
    args=Argument(
        name="files",
        description="Specify files or directories to analyze (overrides config file)",
        is_variadic=True,
        is_optional=True,
    ),
)

__all__ = ["PYRIGHT_SPEC"]
