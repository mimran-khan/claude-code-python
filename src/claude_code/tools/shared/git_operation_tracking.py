"""
Shell-agnostic git operation detection for metrics and summaries.

Migrated from: tools/shared/gitOperationTracking.ts
"""

from __future__ import annotations

import re
from collections.abc import Callable
from dataclasses import dataclass
from typing import Literal

CommitKind = Literal["committed", "amended", "cherry-picked"]
BranchAction = Literal["merged", "rebased"]
PrAction = Literal["created", "edited", "merged", "commented", "closed", "ready"]


def _git_cmd_re(subcmd: str, suffix: str = "") -> re.Pattern[str]:
    return re.compile(
        rf"\bgit(?:\s+-[cC]\s+\S+|\s+--\S+=\S+)*\s+{subcmd}\b{suffix}",
    )


GIT_COMMIT_RE = _git_cmd_re("commit")
GIT_PUSH_RE = _git_cmd_re("push")
GIT_CHERRY_PICK_RE = _git_cmd_re("cherry-pick")
GIT_MERGE_RE = _git_cmd_re("merge", r"(?!-)")
GIT_REBASE_RE = _git_cmd_re("rebase")

_GH_PR_ACTIONS: list[tuple[re.Pattern[str], PrAction, str]] = [
    (re.compile(r"\bgh\s+pr\s+create\b"), "created", "pr_create"),
    (re.compile(r"\bgh\s+pr\s+edit\b"), "edited", "pr_edit"),
    (re.compile(r"\bgh\s+pr\s+merge\b"), "merged", "pr_merge"),
    (re.compile(r"\bgh\s+pr\s+comment\b"), "commented", "pr_comment"),
    (re.compile(r"\bgh\s+pr\s+close\b"), "closed", "pr_close"),
    (re.compile(r"\bgh\s+pr\s+ready\b"), "ready", "pr_ready"),
]


def parse_git_commit_id(stdout: str) -> str | None:
    match = re.search(r"\[[\w./-]+(?: \(root-commit\))? ([0-9a-f]+)\]", stdout)
    return match.group(1) if match else None


def _parse_pr_url(url: str) -> tuple[int, str, str] | None:
    m = re.match(r"https://github\.com/([^/]+/[^/]+)/pull/(\d+)", url)
    if not m:
        return None
    return int(m.group(2), 10), url, m.group(1)


def _find_pr_in_stdout(stdout: str) -> tuple[int, str, str] | None:
    m = re.search(r"https://github\.com/[^\s/]+/[^\s/]+/pull/\d+", stdout)
    return _parse_pr_url(m.group(0)) if m else None


def parse_git_push_branch(output: str) -> str | None:
    m = re.search(
        r"^\s*[+\-*!= ]?\s*(?:\[new branch\]|\S+\.\.+\S+)\s+\S+\s*->\s*(\S+)",
        output,
        re.MULTILINE,
    )
    return m.group(1) if m else None


def _parse_pr_number_from_text(stdout: str) -> int | None:
    m = re.search(r"[Pp]ull request (?:\S+#)?#?(\d+)", stdout)
    return int(m.group(1), 10) if m else None


def _parse_ref_from_command(command: str, verb: str) -> str | None:
    m = _git_cmd_re(verb).search(command)
    if not m:
        return None
    after = command[m.end() :].strip()
    for tok in after.split():
        if re.match(r"^[&|;><]", tok):
            break
        if tok.startswith("-"):
            continue
        return tok
    return None


@dataclass
class GitCommitInfo:
    sha: str
    kind: CommitKind


@dataclass
class GitPushInfo:
    branch: str


@dataclass
class GitBranchInfo:
    ref: str
    action: BranchAction


@dataclass
class GitPrInfo:
    number: int
    action: PrAction
    url: str | None = None


@dataclass
class GitOperationDetectResult:
    commit: GitCommitInfo | None = None
    push: GitPushInfo | None = None
    branch: GitBranchInfo | None = None
    pr: GitPrInfo | None = None


def detect_git_operation(command: str, output: str) -> GitOperationDetectResult:
    result = GitOperationDetectResult()
    is_cherry = bool(GIT_CHERRY_PICK_RE.search(command))
    if GIT_COMMIT_RE.search(command) or is_cherry:
        sha = parse_git_commit_id(output)
        if sha:
            if is_cherry:
                kind: CommitKind = "cherry-picked"
            elif re.search(r"--amend\b", command):
                kind = "amended"
            else:
                kind = "committed"
            result.commit = GitCommitInfo(sha=sha[:6], kind=kind)
    if GIT_PUSH_RE.search(command):
        branch = parse_git_push_branch(output)
        if branch:
            result.push = GitPushInfo(branch=branch)
    if GIT_MERGE_RE.search(command) and re.search(
        r"(Fast-forward|Merge made by)",
        output,
    ):
        ref = _parse_ref_from_command(command, "merge")
        if ref:
            result.branch = GitBranchInfo(ref=ref, action="merged")
    if GIT_REBASE_RE.search(command) and "Successfully rebased" in output:
        ref = _parse_ref_from_command(command, "rebase")
        if ref:
            result.branch = GitBranchInfo(ref=ref, action="rebased")
    for pattern, action, _op in _GH_PR_ACTIONS:
        if pattern.search(command):
            pr = _find_pr_in_stdout(output)
            if pr:
                num, url, _repo = pr
                result.pr = GitPrInfo(number=num, url=url, action=action)
            else:
                num = _parse_pr_number_from_text(output)
                if num is not None:
                    result.pr = GitPrInfo(number=num, action=action)
            break
    return result


def track_git_operations(
    command: str,
    exit_code: int,
    stdout: str | None = None,
    *,
    log_event: Callable[[str, dict[str, object]], None] | None = None,
    increment_commit_counter: Callable[[], None] | None = None,
    increment_pr_counter: Callable[[], None] | None = None,
    link_session_to_pr: Callable[..., None] | None = None,
    get_session_id: Callable[[], str | None] | None = None,
) -> None:
    """
    Increment counters and emit analytics-style events when git/gh operations succeed.

    Full session linking is optional — pass callables wired to your app state.
    """
    if exit_code != 0:
        return

    def _log(name: str, meta: dict[str, object]) -> None:
        if log_event:
            log_event(name, meta)

    if GIT_COMMIT_RE.search(command):
        _log("tengu_git_operation", {"operation": "commit"})
        if re.search(r"--amend\b", command):
            _log("tengu_git_operation", {"operation": "commit_amend"})
        if increment_commit_counter:
            increment_commit_counter()
    if GIT_PUSH_RE.search(command):
        _log("tengu_git_operation", {"operation": "push"})
    pr_hit = next((x for x in _GH_PR_ACTIONS if x[0].search(command)), None)
    if pr_hit:
        _log("tengu_git_operation", {"operation": pr_hit[2]})
    if pr_hit and pr_hit[1] == "created" and stdout and increment_pr_counter:
        pr_info = _find_pr_in_stdout(stdout)
        if pr_info:
            increment_pr_counter()
            if link_session_to_pr and get_session_id:
                sid = get_session_id()
                if sid:
                    num, url, repo = pr_info
                    link_session_to_pr(sid, num, url, repo)
    if re.search(r"\bglab\s+mr\s+create\b", command):
        _log("tengu_git_operation", {"operation": "pr_create"})
        if increment_pr_counter:
            increment_pr_counter()
    is_curl_post = bool(re.search(r"\bcurl\b", command)) and bool(
        re.search(r"-X\s*POST\b|--request\s*=?\s*POST\b|\s-d\s", command, re.I),
    )
    is_pr_endpoint = bool(
        re.search(
            r"https?://[^\s'\"]+/(pulls|pull-requests|merge[-_]requests)(?!/\d)",
            command,
            re.I,
        ),
    )
    if is_curl_post and is_pr_endpoint:
        _log("tengu_git_operation", {"operation": "pr_create"})
        if increment_pr_counter:
            increment_pr_counter()
