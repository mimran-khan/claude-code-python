"""
Migrated from: commands/review.ts
"""

from __future__ import annotations

from dataclasses import dataclass

from ..base import Command, CommandContext, CommandResult

CCR_TERMS_URL = "https://code.claude.com/docs/en/claude-code-on-the-web"


def local_review_prompt(args: str) -> str:
    return f"""
      You are an expert code reviewer. Follow these steps:

      1. If no PR number is provided in the args, run `gh pr list` to show open PRs
      2. If a PR number is provided, run `gh pr view <number>` to get PR details
      3. Run `gh pr diff <number>` to get the diff
      4. Analyze the changes and provide a thorough code review that includes:
         - Overview of what the PR does
         - Analysis of code quality and style
         - Specific suggestions for improvements
         - Any potential issues or risks

      Keep your review concise but thorough. Focus on:
      - Code correctness
      - Following project conventions
      - Performance implications
      - Test coverage
      - Security considerations

      Format your review with clear sections and bullet points.

      PR number: {args}
    """


@dataclass(frozen=True)
class PromptTextBlock:
    type: str = "text"
    text: str = ""


class ReviewCommand(Command):
    @property
    def name(self) -> str:
        return "review"

    @property
    def description(self) -> str:
        return "Review a pull request"

    @property
    def command_type(self):
        return "prompt"  # type: ignore[return-value]

    async def get_prompt_blocks(self, args: str) -> list[PromptTextBlock]:
        return [PromptTextBlock(text=local_review_prompt(args))]

    async def execute(self, context: CommandContext) -> CommandResult:
        arg_str = " ".join(context.args)
        blocks = await self.get_prompt_blocks(arg_str)
        return CommandResult(
            success=True,
            output={
                "progress_message": "reviewing pull request",
                "source": "builtin",
                "prompt_blocks": [b.__dict__ for b in blocks],
            },
        )


class UltrareviewCommand(Command):
    def __init__(self, *, ultrareview_enabled: bool = False) -> None:
        self._enabled = ultrareview_enabled

    @property
    def name(self) -> str:
        return "ultrareview"

    @property
    def description(self) -> str:
        return (
            f"~10–20 min · Finds and verifies bugs in your branch. Runs in Claude Code on the web. See {CCR_TERMS_URL}"
        )

    @property
    def command_type(self):
        return "local-jsx"  # type: ignore[return-value]

    async def execute(self, context: CommandContext) -> CommandResult:
        if not self._enabled:
            return CommandResult(success=False, message="Ultrareview not enabled.")
        return CommandResult(
            success=True,
            output={"action": "load_jsx", "module": "ultrareviewCommand"},
        )
