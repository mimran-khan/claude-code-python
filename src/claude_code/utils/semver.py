"""
Semver comparison using ``packaging.version`` (Python equivalent of Bun.semver / npm semver).

Migrated from: utils/semver.ts
"""

from __future__ import annotations

from packaging.version import Version, parse


def _v(a: str) -> Version:
    return parse(a)


def gt(a: str, b: str) -> bool:
    return _v(a) > _v(b)


def gte(a: str, b: str) -> bool:
    return _v(a) >= _v(b)


def lt(a: str, b: str) -> bool:
    return _v(a) < _v(b)


def lte(a: str, b: str) -> bool:
    return _v(a) <= _v(b)


def order(a: str, b: str) -> int:
    va, vb = _v(a), _v(b)
    if va < vb:
        return -1
    if va > vb:
        return 1
    return 0


def satisfies(version: str, spec: str) -> bool:
    """Return True if ``version`` satisfies the PEP 440 / npm-style ``spec`` string."""
    from packaging.specifiers import SpecifierSet

    try:
        spec_set = SpecifierSet(spec, prereleases=True)
        return spec_set.contains(Version(version), prereleases=True)
    except Exception:
        return False
