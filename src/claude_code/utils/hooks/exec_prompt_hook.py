"""
Execute user-configured prompt hooks (stub for subprocess integration).

Migrated from: utils/hooks/execPromptHook.ts
"""

from __future__ import annotations

from dataclasses import dataclass


@dataclass
class PromptHookResult:
    ok: bool
    stdout: str = ""
    stderr: str = ""
    exit_code: int = 0


async def exec_prompt_hook(command: list[str], env: dict[str, str] | None = None) -> PromptHookResult:
    import asyncio

    try:
        proc = await asyncio.create_subprocess_exec(
            *command,
            env={**__import__("os").environ, **(env or {})},
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE,
        )
        out_b, err_b = await proc.communicate()
        return PromptHookResult(
            ok=proc.returncode == 0,
            stdout=out_b.decode(errors="replace"),
            stderr=err_b.decode(errors="replace"),
            exit_code=proc.returncode or 0,
        )
    except Exception as e:
        return PromptHookResult(ok=False, stderr=str(e), exit_code=-1)
