"""Tests for constants migrated from TypeScript."""

from __future__ import annotations

import pytest

from claude_code.bootstrap.state import (
    clear_system_prompt_section_state,
    get_system_prompt_section_cache,
)
from claude_code.constants.cyber_risk_instruction import CYBER_RISK_INSTRUCTION
from claude_code.constants.github_app import PR_TITLE, WORKFLOW_CONTENT
from claude_code.constants.keys import get_growth_book_client_key
from claude_code.constants.prompts import (
    CLAUDE_CODE_DOCS_MAP_URL,
    SYSTEM_PROMPT_DYNAMIC_BOUNDARY,
    prepend_bullets,
)
from claude_code.constants.spinner_verbs import SPINNER_VERBS, get_spinner_verbs
from claude_code.constants.system_prompt_sections import (
    clear_system_prompt_sections,
    resolve_system_prompt_sections,
    system_prompt_section,
)
from claude_code.constants.turn_completion_verbs import TURN_COMPLETION_VERBS


def test_cyber_risk_instruction_non_empty() -> None:
    assert "authorized security testing" in CYBER_RISK_INSTRUCTION


def test_github_app_strings() -> None:
    assert "Claude Code" in PR_TITLE
    assert "anthropics/claude-code-action" in WORKFLOW_CONTENT
    assert "${{ secrets.ANTHROPIC_API_KEY }}" in WORKFLOW_CONTENT


def test_prompt_constants() -> None:
    assert "claude_code_docs_map" in CLAUDE_CODE_DOCS_MAP_URL
    assert SYSTEM_PROMPT_DYNAMIC_BOUNDARY.startswith("__SYSTEM_")


def test_prepend_bullets() -> None:
    assert prepend_bullets(["a", ("b", "c")]) == [" - a", "  - b", "  - c"]


def test_spinner_verbs_default_count() -> None:
    assert len(SPINNER_VERBS) == 187
    assert get_spinner_verbs()[0] == SPINNER_VERBS[0]


def test_turn_completion_verbs() -> None:
    assert "Worked" in TURN_COMPLETION_VERBS


def test_get_growth_book_client_key_ant_dev(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("USER_TYPE", "ant")
    monkeypatch.setenv("ENABLE_GROWTHBOOK_DEV", "1")
    assert get_growth_book_client_key() == "sdk-yZQvlplybuXjYh6L"


def test_get_growth_book_client_key_ant_prod(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("USER_TYPE", "ant")
    monkeypatch.delenv("ENABLE_GROWTHBOOK_DEV", raising=False)
    assert get_growth_book_client_key() == "sdk-xRVcrliHIlrg4og4"


def test_get_growth_book_client_key_public(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.delenv("USER_TYPE", raising=False)
    assert get_growth_book_client_key() == "sdk-zAZezfDKGoZuXXKe"


@pytest.mark.asyncio
async def test_resolve_system_prompt_sections_caches() -> None:
    clear_system_prompt_section_state()
    calls = {"n": 0}

    def compute() -> str:
        calls["n"] += 1
        return "x"

    sections = [system_prompt_section("s1", compute)]
    out1 = await resolve_system_prompt_sections(sections)
    out2 = await resolve_system_prompt_sections(sections)
    assert out1 == ["x"] and out2 == ["x"]
    assert calls["n"] == 1
    assert get_system_prompt_section_cache()["s1"] == "x"
    clear_system_prompt_sections()
