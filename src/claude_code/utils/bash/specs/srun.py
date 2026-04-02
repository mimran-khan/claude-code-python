"""Built-in ``srun`` command spec. Migrated from: utils/bash/specs/srun.ts"""

from __future__ import annotations

from ..command_spec import Argument, CommandSpec, Option

SRUN_SPEC = CommandSpec(
    name="srun",
    description="Run a command on SLURM cluster nodes",
    options=[
        Option(
            name=["-n", "--ntasks"],
            description="Number of tasks",
            args=Argument(name="count", description="Number of tasks to run"),
        ),
        Option(
            name=["-N", "--nodes"],
            description="Number of nodes",
            args=Argument(name="count", description="Number of nodes to allocate"),
        ),
    ],
    args=Argument(
        name="command",
        description="Command to run on the cluster",
        is_command=True,
    ),
)

__all__ = ["SRUN_SPEC"]
