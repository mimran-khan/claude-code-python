"""
Curated secret patterns for team memory pre-upload scan.

Migrated from: services/teamMemorySync/secretScanner.ts (regex sources aligned with gitleaks).
"""

from __future__ import annotations

import re
from dataclasses import dataclass

from ...utils.strings import capitalize


@dataclass(frozen=True)
class SecretMatch:
    rule_id: str
    label: str


_ANT_KEY_PFX = "-".join(("sk", "ant", "api"))

# (id, pattern, flags) — patterns are JavaScript-compatible literals transcribed to Python
_SECRET_RULES: list[tuple[str, str, int]] = [
    ("aws-access-token", r"\b((?:A3T[A-Z0-9]|AKIA|ASIA|ABIA|ACCA)[A-Z2-7]{16})\b", 0),
    ("gcp-api-key", r"\b(AIza[\w-]{35})(?:[`'\"\s;]|\\[nr]|$)", 0),
    ("github-pat", r"ghp_[0-9a-zA-Z]{36}", 0),
    ("github-fine-grained-pat", r"github_pat_\w{82}", 0),
    ("gitlab-pat", r"glpat-[\w-]{20}", 0),
    ("slack-bot-token", r"xoxb-[0-9]{10,13}-[0-9]{10,13}[a-zA-Z0-9-]*", 0),
    ("npm-access-token", r"\b(npm_[a-zA-Z0-9]{36})(?:[`'\"\s;]|\\[nr]|$)", 0),
    (
        "anthropic-api-key",
        rf"\b({_ANT_KEY_PFX}03-[a-zA-Z0-9_\-]{{93}}AA)(?:[`'\"\s;]|\\[nr]|$)",
        0,
    ),
    ("openai-api-key", r"\bsk-[a-zA-Z0-9]{20,}T3BlbkFJ[a-zA-Z0-9]{20,}", 0),
    (
        "stripe-access-token",
        r"\b((?:sk|rk)_(?:test|live|prod)_[a-zA-Z0-9]{10,99})(?:[`'\"\s;]|\\[nr]|$)",
        0,
    ),
    (
        "private-key",
        r"-----BEGIN[ A-Z0-9_-]{0,100}PRIVATE KEY(?: BLOCK)?-----[\s\S-]{64,}?-----END[ A-Z0-9_-]{0,100}PRIVATE KEY(?: BLOCK)?-----",
        re.IGNORECASE,
    ),
]

_compiled: list[tuple[str, re.Pattern[str]]] | None = None


def _get_compiled() -> list[tuple[str, re.Pattern[str]]]:
    global _compiled
    if _compiled is None:
        _compiled = [(rid, re.compile(src, flags)) for rid, src, flags in _SECRET_RULES]
    return _compiled


_SPECIAL = {
    "aws": "AWS",
    "gcp": "GCP",
    "api": "API",
    "pat": "PAT",
    "oauth": "OAuth",
    "npm": "NPM",
    "pypi": "PyPI",
    "github": "GitHub",
    "gitlab": "GitLab",
    "openai": "OpenAI",
}


def _rule_id_to_label(rule_id: str) -> str:
    return " ".join(_SPECIAL.get(p, capitalize(p)) for p in rule_id.split("-"))


def scan_for_secrets(content: str) -> list[SecretMatch]:
    matches: list[SecretMatch] = []
    seen: set[str] = set()
    for rule_id, pattern in _get_compiled():
        if rule_id in seen:
            continue
        if pattern.search(content):
            seen.add(rule_id)
            matches.append(SecretMatch(rule_id=rule_id, label=_rule_id_to_label(rule_id)))
    return matches


def get_secret_label(rule_id: str) -> str:
    return _rule_id_to_label(rule_id)
