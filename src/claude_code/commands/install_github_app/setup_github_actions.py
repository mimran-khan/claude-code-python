"""
GitHub Actions setup for Claude.

Migrated from: commands/install-github-app/setupGitHubActions.ts

Uses `gh` CLI via asyncio subprocess (parity with execFileNoThrow).
"""

from __future__ import annotations

import asyncio
import base64
import logging
import time
from collections.abc import Awaitable, Callable
from dataclasses import dataclass
from urllib.parse import quote

from .types import Workflow
from .workflow_templates import (
    CODE_REVIEW_PLUGIN_WORKFLOW_CONTENT,
    PR_BODY,
    PR_TITLE,
    WORKFLOW_CONTENT,
)

logger = logging.getLogger(__name__)


@dataclass
class GitHubActionsSetupContext:
    use_current_repo: bool | None = None
    workflow_exists: bool | None = None
    secret_exists: bool | None = None


async def _run_gh(args: list[str]) -> tuple[int, str, str]:
    proc = await asyncio.create_subprocess_exec(
        "gh",
        *args,
        stdout=asyncio.subprocess.PIPE,
        stderr=asyncio.subprocess.PIPE,
    )
    out_b, err_b = await proc.communicate()
    code = proc.returncode if proc.returncode is not None else -1
    return code, out_b.decode(errors="replace"), err_b.decode(errors="replace")


def _adjust_workflow_content(workflow_content: str, secret_name: str) -> str:
    content = workflow_content
    if secret_name == "CLAUDE_CODE_OAUTH_TOKEN":
        content = content.replace(
            "anthropic_api_key: ${{ secrets.ANTHROPIC_API_KEY }}",
            "claude_code_oauth_token: ${{ secrets.CLAUDE_CODE_OAUTH_TOKEN }}",
        )
    elif secret_name != "ANTHROPIC_API_KEY":
        content = content.replace(
            "anthropic_api_key: ${{ secrets.ANTHROPIC_API_KEY }}",
            f"anthropic_api_key: ${{ secrets.{secret_name} }}",
        )
    return content


async def _create_workflow_file(
    repo_name: str,
    branch_name: str,
    workflow_path: str,
    workflow_content: str,
    secret_name: str,
    message: str,
    context: GitHubActionsSetupContext | None = None,
) -> None:
    check_code, check_out, _ = await _run_gh(
        [
            "api",
            f"repos/{repo_name}/contents/{workflow_path}",
            "--jq",
            ".sha",
        ],
    )
    file_sha: str | None = None
    if check_code == 0:
        file_sha = check_out.strip()

    content = _adjust_workflow_content(workflow_content, secret_name)
    b64 = base64.b64encode(content.encode("utf-8")).decode("ascii")

    msg = f"Update {message}" if file_sha else message
    api_params = [
        "api",
        "--method",
        "PUT",
        f"repos/{repo_name}/contents/{workflow_path}",
        "-f",
        f"message={msg}",
        "-f",
        f"content={b64}",
        "-f",
        f"branch={branch_name}",
    ]
    if file_sha:
        api_params.extend(["-f", f"sha={file_sha}"])

    create_code, _, create_err = await _run_gh(api_params)
    if create_code != 0:
        if "422" in create_err and "sha" in create_err:
            raise RuntimeError(
                f"Failed to create workflow file {workflow_path}: "
                "A Claude workflow file already exists in this repository. "
                "Please remove it first or update it manually.",
            ) from None
        help_text = (
            "\n\nNeed help? Common issues:\n"
            "· Permission denied → Run: gh auth refresh -h github.com -s repo,workflow\n"
            "· Not authorized → Ensure you have admin access to the repository\n"
            "· For manual setup → Visit: https://github.com/anthropics/claude-code-action"
        )
        raise RuntimeError(
            f"Failed to create workflow file {workflow_path}: {create_err}{help_text}",
        ) from None
    if context:
        logger.debug("workflow context %s", context)


async def setup_github_actions(
    repo_name: str,
    api_key_or_oauth_token: str | None,
    secret_name: str,
    update_progress: Callable[[], None],
    skip_workflow: bool = False,
    selected_workflows: list[Workflow] | None = None,
    auth_type: str = "api_key",
    context: GitHubActionsSetupContext | None = None,
    open_browser: Callable[[str], bool | Awaitable[bool]] | None = None,
    save_global_config_increment: Callable[[], None] | None = None,
) -> None:
    if selected_workflows is None:
        selected_workflows = ["claude", "claude-review"]

    repo_check_code, _, repo_err = await _run_gh(
        ["api", f"repos/{repo_name}", "--jq", ".id"],
    )
    if repo_check_code != 0:
        raise RuntimeError(
            f"Failed to access repository {repo_name}: {repo_err}",
        ) from None

    branch_code, branch_out, branch_err = await _run_gh(
        ["api", f"repos/{repo_name}", "--jq", ".default_branch"],
    )
    if branch_code != 0:
        raise RuntimeError(
            f"Failed to get default branch: {branch_err}",
        ) from None
    default_branch = branch_out.strip()

    sha_code, sha_out, sha_err = await _run_gh(
        [
            "api",
            f"repos/{repo_name}/git/ref/heads/{default_branch}",
            "--jq",
            ".object.sha",
        ],
    )
    if sha_code != 0:
        raise RuntimeError(f"Failed to get branch SHA: {sha_err}") from None
    sha = sha_out.strip()

    branch_name: str | None = None
    if not skip_workflow:
        update_progress()
        branch_name = f"add-claude-github-actions-{int(time.time() * 1000)}"
        create_branch_code, _, cb_err = await _run_gh(
            [
                "api",
                "--method",
                "POST",
                f"repos/{repo_name}/git/refs",
                "-f",
                f"ref=refs/heads/{branch_name}",
                "-f",
                f"sha={sha}",
            ],
        )
        if create_branch_code != 0:
            raise RuntimeError(f"Failed to create branch: {cb_err}") from None

        update_progress()
        workflows: list[tuple[str, str, str]] = []
        if "claude" in selected_workflows:
            workflows.append(
                (
                    ".github/workflows/claude.yml",
                    WORKFLOW_CONTENT,
                    "Claude PR Assistant workflow",
                ),
            )
        if "claude-review" in selected_workflows:
            workflows.append(
                (
                    ".github/workflows/claude-code-review.yml",
                    CODE_REVIEW_PLUGIN_WORKFLOW_CONTENT,
                    "Claude Code Review workflow",
                ),
            )
        for wf_path, wf_content, wf_message in workflows:
            await _create_workflow_file(
                repo_name,
                branch_name,
                wf_path,
                wf_content,
                secret_name,
                wf_message,
                context,
            )

    update_progress()
    if api_key_or_oauth_token:
        set_secret_code, _, ss_err = await _run_gh(
            [
                "secret",
                "set",
                secret_name,
                "--body",
                api_key_or_oauth_token,
                "--repo",
                repo_name,
            ],
        )
        if set_secret_code != 0:
            help_text = (
                "\n\nNeed help? Common issues:\n"
                "· Permission denied → Run: gh auth refresh -h github.com -s repo\n"
                "· Not authorized → Ensure you have admin access to the repository\n"
                "· For manual setup → Visit: https://github.com/anthropics/claude-code-action"
            )
            raise RuntimeError(
                f"Failed to set API key secret: {ss_err or 'Unknown error'}{help_text}",
            ) from None

    if not skip_workflow and branch_name:
        update_progress()
        compare_url = (
            f"https://github.com/{repo_name}/compare/"
            f"{default_branch}...{branch_name}?quick_pull=1"
            f"&title={quote(PR_TITLE)}&body={quote(PR_BODY)}"
        )
        if open_browser is not None:
            res = open_browser(compare_url)
            if asyncio.iscoroutine(res):
                await res

    if save_global_config_increment:
        save_global_config_increment()
