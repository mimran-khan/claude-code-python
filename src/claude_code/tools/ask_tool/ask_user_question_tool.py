"""
Ask the user multiple-choice questions.

Migrated from: tools/AskUserQuestionTool/AskUserQuestionTool.tsx
"""

from __future__ import annotations

import re
from dataclasses import dataclass, field
from typing import Any

from ...core.tool import (
    Tool,
    ToolCallProgress,
    ToolResult,
    ToolUseContext,
    ValidationResult,
)
from ..exit_plan_mode_tool.constants import EXIT_PLAN_MODE_TOOL_NAME
from .constants import ASK_USER_QUESTION_TOOL_NAME

DESCRIPTION = (
    "Asks the user multiple choice questions to gather information, clarify ambiguity, "
    "understand preferences, make decisions or offer them choices."
)

_PRE_MARKDOWN = """
Preview feature (markdown):
Use optional `preview` on options for side-by-side comparisons (mockups, snippets, diagrams).
Previews are only for single-select questions.
"""

_PRE_HTML = """
Preview feature (html):
Optional `preview` must be a self-contained HTML fragment (no script/style tags).
Previews are only for single-select questions.
"""

ASK_USER_QUESTION_TOOL_PROMPT = f"""Use this tool when you need to ask the user questions during execution.
Plan mode: clarify before planning; for approval use {EXIT_PLAN_MODE_TOOL_NAME}, not this tool.
Do not ask the user about "the plan" in the UI sense — use {EXIT_PLAN_MODE_TOOL_NAME} when appropriate.
"""


def get_ask_user_question_prompt(preview_format: str | None) -> str:
    if preview_format == "markdown":
        return ASK_USER_QUESTION_TOOL_PROMPT + _PRE_MARKDOWN
    if preview_format == "html":
        return ASK_USER_QUESTION_TOOL_PROMPT + _PRE_HTML
    return ASK_USER_QUESTION_TOOL_PROMPT


@dataclass
class QuestionOption:
    label: str
    description: str
    preview: str | None = None


@dataclass
class Question:
    question: str
    header: str
    options: list[QuestionOption]
    multi_select: bool = False


@dataclass
class QuestionAnnotation:
    preview: str | None = None
    notes: str | None = None


@dataclass
class AskUserQuestionOutput:
    questions: list[Question]
    answers: dict[str, str]
    annotations: dict[str, QuestionAnnotation] = field(default_factory=dict)


def _questions_from_input(raw: list[dict[str, Any]]) -> list[Question]:
    out: list[Question] = []
    for q in raw:
        opts_raw = q.get("options") or []
        options: list[QuestionOption] = []
        for o in opts_raw:
            if not isinstance(o, dict):
                continue
            options.append(
                QuestionOption(
                    label=str(o.get("label", "")),
                    description=str(o.get("description", "")),
                    preview=o.get("preview") if isinstance(o.get("preview"), str) else None,
                ),
            )
        out.append(
            Question(
                question=str(q.get("question", "")),
                header=str(q.get("header", "")),
                options=options,
                multi_select=bool(q.get("multiSelect", q.get("multi_select", False))),
            ),
        )
    return out


def _validate_uniqueness(questions: list[Question]) -> str | None:
    texts = [q.question for q in questions]
    if len(texts) != len(set(texts)):
        return "Question texts must be unique"
    for q in questions:
        labels = [o.label for o in q.options]
        if len(labels) != len(set(labels)):
            return "Option labels must be unique within each question"
    return None


def validate_html_preview(preview: str | None) -> str | None:
    """Lightweight HTML fragment check (TS validateHtmlPreview)."""
    if preview is None:
        return None
    if re.search(r"<\s*(html|body|!doctype)\b", preview, re.I):
        return "preview must be an HTML fragment, not a full document (no <html>, <body>, or <!DOCTYPE>)"
    if re.search(r"<\s*(script|style)\b", preview, re.I):
        return "preview must not contain <script> or <style> tags"
    if not re.search(r"<[a-z][^>]*>", preview, re.I):
        return "preview must contain HTML (wrap content in a tag like <div> or <pre>)"
    return None


INPUT_SCHEMA: dict[str, Any] = {
    "type": "object",
    "additionalProperties": False,
    "properties": {
        "questions": {
            "type": "array",
            "minItems": 1,
            "maxItems": 4,
            "items": {
                "type": "object",
                "additionalProperties": False,
                "properties": {
                    "question": {"type": "string"},
                    "header": {"type": "string"},
                    "options": {
                        "type": "array",
                        "minItems": 2,
                        "maxItems": 4,
                        "items": {
                            "type": "object",
                            "additionalProperties": False,
                            "properties": {
                                "label": {"type": "string"},
                                "description": {"type": "string"},
                                "preview": {"type": "string"},
                            },
                            "required": ["label", "description"],
                        },
                    },
                    "multiSelect": {"type": "boolean", "default": False},
                },
                "required": ["question", "header", "options"],
            },
        },
        "answers": {
            "type": "object",
            "additionalProperties": {"type": "string"},
            "description": "Filled by permission / UI layer before call completes",
        },
        "annotations": {"type": "object"},
        "metadata": {"type": "object"},
        "question_preview_format": {
            "type": "string",
            "enum": ["html", "markdown"],
            "description": "Host injects preview format for HTML validation (optional).",
        },
    },
    "required": ["questions"],
}


class AskUserQuestionTool(Tool):
    """Interactive multiple-choice questions (requires user interaction in host)."""

    name = ASK_USER_QUESTION_TOOL_NAME
    description = DESCRIPTION
    input_schema = INPUT_SCHEMA
    is_read_only = True
    is_concurrency_safe = True
    user_facing_name = ""

    def validate_input(self, input_data: dict[str, Any]) -> ValidationResult:
        raw_q = input_data.get("questions")
        if not isinstance(raw_q, list) or not raw_q:
            return ValidationResult(result=False, message="questions must be a non-empty array", error_code=1)
        questions = _questions_from_input(raw_q)
        msg = _validate_uniqueness(questions)
        if msg:
            return ValidationResult(result=False, message=msg, error_code=1)

        fmt = input_data.get("question_preview_format")
        if isinstance(fmt, str) and fmt == "html":
            for q in questions:
                for opt in q.options:
                    err = validate_html_preview(opt.preview)
                    if err:
                        return ValidationResult(
                            result=False,
                            message=f'Option "{opt.label}" in question "{q.question}": {err}',
                            error_code=1,
                        )
        return ValidationResult(result=True)

    async def call(
        self,
        input_data: dict[str, Any],
        context: ToolUseContext,
        progress_callback: ToolCallProgress | None = None,
    ) -> ToolResult[AskUserQuestionOutput]:
        _ = progress_callback
        raw_q = input_data.get("questions") or []
        questions = _questions_from_input(raw_q if isinstance(raw_q, list) else [])
        answers_raw = input_data.get("answers") or {}
        answers: dict[str, str] = (
            {str(k): str(v) for k, v in answers_raw.items()} if isinstance(answers_raw, dict) else {}
        )

        annotations: dict[str, QuestionAnnotation] = {}
        ann_raw = input_data.get("annotations")
        if isinstance(ann_raw, dict):
            for k, v in ann_raw.items():
                if isinstance(v, dict):
                    annotations[str(k)] = QuestionAnnotation(
                        preview=v.get("preview") if isinstance(v.get("preview"), str) else None,
                        notes=v.get("notes") if isinstance(v.get("notes"), str) else None,
                    )

        # TODO: Host must inject `answers` via permission flow (TS requiresUserInteraction).
        return ToolResult(
            data=AskUserQuestionOutput(
                questions=questions,
                answers=answers,
                annotations=annotations,
            ),
        )

    def get_tool_use_summary(self, input_data: dict[str, Any]) -> str:
        qs = input_data.get("questions")
        if isinstance(qs, list) and qs:
            first = qs[0]
            if isinstance(first, dict) and first.get("question"):
                return str(first["question"])[:120]
        return ASK_USER_QUESTION_TOOL_NAME


def tool_documentation_prompt(context_options: dict[str, Any] | None = None) -> str:
    """Full model-facing prompt including optional preview format."""
    fmt = None
    if isinstance(context_options, dict):
        fmt = context_options.get("question_preview_format")
    return get_ask_user_question_prompt(fmt if isinstance(fmt, str) else None)
