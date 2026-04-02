"""Types for Constrained Language Mode awareness (PowerShell).

Migrated from: tools/PowerShellTool/clmTypes.ts (simplified).
"""

from __future__ import annotations

from dataclasses import dataclass
from enum import StrEnum


class LanguageMode(StrEnum):
    FULL_LANGUAGE = "FullLanguage"
    CONSTRAINED_LANGUAGE = "ConstrainedLanguage"
    RESTRICTED_LANGUAGE = "RestrictedLanguage"


@dataclass
class ClmInspectionResult:
    mode: LanguageMode
    detail: str = ""
