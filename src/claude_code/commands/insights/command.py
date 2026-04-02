"""
Migrated from: commands/insights.ts (usageReport command).
"""

from __future__ import annotations

import json
import os
from collections.abc import Awaitable, Callable
from dataclasses import dataclass

from ..base import Command, CommandContext, CommandResult
from .generate_report import (
    GenerateUsageReportOptions,
    generate_usage_report,
    get_facets_dir,
)
from .types import InsightsPayload


@dataclass(frozen=True)
class PromptTextBlock:
    type: str = "text"
    text: str = ""


async def get_running_remote_hosts_stub() -> list[str]:
    return []


async def build_insights_prompt(
    args_joined: str,
    *,
    user_type: str | None = None,
    get_running_remote_hosts: Callable[[], Awaitable[list[str]]] | None = None,
) -> list[PromptTextBlock]:
    ut = user_type or os.environ.get("USER_TYPE", "")
    collect_remote = "--homespaces" in args_joined if ut == "ant" else False
    hosts_fn = get_running_remote_hosts or get_running_remote_hosts_stub
    remote_hosts = await hosts_fn() if ut == "ant" else []
    has_remote = len(remote_hosts) > 0

    result = await generate_usage_report(
        GenerateUsageReportOptions(collect_remote=collect_remote),
    )

    insights: InsightsPayload = result.insights
    html_path = result.html_path
    data = result.data
    remote_stats = result.remote_stats

    report_url = f"file://{html_path}"
    upload_hint = ""

    session_label = (
        f"{data.total_sessions_scanned} sessions total · {data.total_sessions} analyzed"
        if data.total_sessions_scanned and data.total_sessions_scanned > data.total_sessions
        else f"{data.total_sessions} sessions"
    )
    stats = " · ".join(
        [
            session_label,
            f"{data.total_messages:,} messages",
            f"{round(data.total_duration_hours)}h",
            f"{data.git_commits} commits",
        ],
    )

    remote_info = ""
    if ut == "ant" and remote_stats and remote_stats.total_copied > 0:
        hs_names = ", ".join(h.name for h in remote_stats.hosts if h.session_count > 0)
        remote_info = f"\n_Collected {remote_stats.total_copied} new sessions from: {hs_names}_\n"
    elif ut == "ant" and not collect_remote and has_remote:
        remote_info = (
            f"\n_Tip: Run `/insights --homespaces` to include sessions from your "
            f"{len(remote_hosts)} running homespace(s)_\n"
        )

    at_glance = insights.at_a_glance
    parts: list[str] = ["## At a Glance", ""]
    if at_glance:
        if at_glance.whats_working:
            parts.append(
                f"**What's working:** {at_glance.whats_working} See _Impressive Things You Did_.\n",
            )
        if at_glance.whats_hindering:
            parts.append(
                f"**What's hindering you:** {at_glance.whats_hindering} See _Where Things Go Wrong_.\n",
            )
        if at_glance.quick_wins:
            parts.append(
                f"**Quick wins to try:** {at_glance.quick_wins} See _Features to Try_.\n",
            )
        if at_glance.ambitious_workflows:
            parts.append(
                f"**Ambitious workflows:** {at_glance.ambitious_workflows} See _On the Horizon_.\n",
            )
    summary_text = "".join(parts).strip() or "_No insights generated_"

    header = f"""# Claude Code Insights

{stats}
{data.date_range.start} to {data.date_range.end}
{remote_info}
"""
    user_summary = f"{header}{summary_text}\n\nYour full shareable insights report is ready: {report_url}{upload_hint}"

    payload = insights.raw if insights.raw else {}
    intro = "The user just ran /insights to generate a usage report analyzing their Claude Code sessions."
    prompt_body = f"""{intro}

Here is the full insights data:
{json.dumps(payload, indent=2)}

Report URL: {report_url}
HTML file: {html_path}
Facets directory: {get_facets_dir()}

Here is what the user sees:
{user_summary}

Now output the following message exactly:

<message>
Your shareable insights report is ready:
{report_url}{upload_hint}

Want to dig into any section or try one of the suggestions?
</message>"""

    return [PromptTextBlock(text=prompt_body)]


class InsightsCommand(Command):
    @property
    def name(self) -> str:
        return "insights"

    @property
    def description(self) -> str:
        return "Generate a report analyzing your Claude Code sessions"

    @property
    def command_type(self):
        return "prompt"  # type: ignore[return-value]

    async def execute(self, context: CommandContext) -> CommandResult:
        args_joined = " ".join(context.args)
        blocks = await build_insights_prompt(args_joined)
        return CommandResult(
            success=True,
            output={
                "progress_message": "analyzing your sessions",
                "source": "builtin",
                "prompt_blocks": [b.__dict__ for b in blocks],
            },
        )
