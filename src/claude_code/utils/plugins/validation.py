"""
Validate plugin.json, marketplace.json, markdown components, and hooks.json.

Migrated from: utils/plugins/validatePlugin.ts
"""

from __future__ import annotations

import asyncio
import json
import os
import re
import stat
from dataclasses import dataclass, field
from typing import Any, Literal

import yaml
from pydantic import BaseModel, ConfigDict, Field
from pydantic import ValidationError as PydanticValidationError

from ..errors import error_message, get_errno_code, is_enoent
from ..json_utils import safe_parse_json

FRONTMATTER_REGEX = re.compile(r"^---\s*\n([\s\S]*?)---\s*\n?")
MARKETPLACE_ONLY_MANIFEST_FIELDS = frozenset({"category", "source", "tags", "strict", "id"})


@dataclass
class ValidationErrorEntry:
    path: str
    message: str
    code: str | None = None


@dataclass
class ValidationWarningEntry:
    path: str
    message: str


@dataclass
class ValidationResult:
    success: bool
    errors: list[ValidationErrorEntry] = field(default_factory=list)
    warnings: list[ValidationWarningEntry] = field(default_factory=list)
    file_path: str = ""
    file_type: Literal["plugin", "marketplace", "skill", "agent", "command", "hooks"] = "plugin"


class PluginManifestStrict(BaseModel):
    model_config = ConfigDict(extra="forbid")

    name: str
    version: str | None = None
    description: str | None = None
    author: str | dict[str, Any] | None = None
    commands: list[str] | str | None = None
    agents: list[str] | str | None = None
    skills: list[str] | str | None = None


class MarketplacePluginEntryStrict(BaseModel):
    model_config = ConfigDict(extra="forbid", populate_by_name=True)

    name: str
    source: str | dict[str, Any]
    version: str | None = None


class MarketplaceManifestStrict(BaseModel):
    model_config = ConfigDict(extra="forbid")

    metadata: dict[str, Any] | None = None
    plugins: list[MarketplacePluginEntryStrict] = Field(default_factory=list)


class PluginHooksStrict(BaseModel):
    model_config = ConfigDict(extra="allow")


def _format_pydantic(err: PydanticValidationError) -> list[ValidationErrorEntry]:
    out: list[ValidationErrorEntry] = []
    for issue in err.errors():
        loc = ".".join(str(x) for x in issue.get("loc", ())) or "root"
        out.append(
            ValidationErrorEntry(
                path=loc,
                message=str(issue.get("msg", "validation error")),
                code=str(issue.get("type", "")),
            )
        )
    return out


def _check_path_traversal(
    p: str,
    field_path: str,
    errors: list[ValidationErrorEntry],
    hint: str | None = None,
) -> None:
    if ".." in p:
        msg = hint or f'Path contains ".." which could be a path traversal attempt: {p}'
        errors.append(ValidationErrorEntry(path=field_path, message=msg))


def _marketplace_source_hint(p: str) -> str:
    stripped = re.sub(r"^(\.\./)+", "", p)
    corrected = f"./{stripped}" if stripped != p else "./plugins/my-plugin"
    return (
        "Plugin source paths are resolved relative to the marketplace root, not "
        f'relative to marketplace.json. Use "{corrected}" instead of "{p}".'
    )


def detect_manifest_type(file_path: str) -> Literal["plugin", "marketplace", "unknown"]:
    base = os.path.basename(file_path)
    parent = os.path.basename(os.path.dirname(file_path))
    if base == "plugin.json":
        return "plugin"
    if base == "marketplace.json":
        return "marketplace"
    if parent == ".claude-plugin":
        return "plugin"
    return "unknown"


async def validate_plugin_manifest(file_path: str) -> ValidationResult:
    errors: list[ValidationErrorEntry] = []
    warnings: list[ValidationWarningEntry] = []
    absolute_path = os.path.abspath(file_path)
    try:
        content = await asyncio.to_thread(
            lambda: open(absolute_path, encoding="utf-8").read(),
        )
    except OSError as e:
        code = get_errno_code(e)
        if code == "ENOENT":
            msg = f"File not found: {absolute_path}"
        elif code == "EISDIR":
            msg = f"Path is not a file: {absolute_path}"
        else:
            msg = f"Failed to read file: {error_message(e)}"
        return ValidationResult(
            success=False,
            errors=[ValidationErrorEntry(path="file", message=msg, code=code)],
            file_path=absolute_path,
            file_type="plugin",
        )

    try:
        parsed: Any = json.loads(content)
    except json.JSONDecodeError as e:
        return ValidationResult(
            success=False,
            errors=[ValidationErrorEntry(path="json", message=f"Invalid JSON syntax: {e}")],
            file_path=absolute_path,
            file_type="plugin",
        )

    if isinstance(parsed, dict):
        obj = dict(parsed)
        for key, label in (("commands", "commands"), ("agents", "agents"), ("skills", "skills")):
            raw = obj.get(key)
            if raw is None:
                continue
            seq = raw if isinstance(raw, list) else [raw]
            for i, item in enumerate(seq):
                if isinstance(item, str):
                    _check_path_traversal(item, f"{label}[{i}]", errors)
        stray = [k for k in obj if k in MARKETPLACE_ONLY_MANIFEST_FIELDS]
        for k in stray:
            warnings.append(
                ValidationWarningEntry(
                    path=k,
                    message=(
                        f"Field '{k}' belongs in marketplace.json, not plugin.json (harmless but unused at load time)."
                    ),
                )
            )
            del obj[k]
        parsed = obj

    try:
        data = PluginManifestStrict.model_validate(parsed)
    except PydanticValidationError as e:
        errors.extend(_format_pydantic(e))
    else:
        if not re.match(r"^[a-z0-9]+(-[a-z0-9]+)*$", data.name):
            warnings.append(
                ValidationWarningEntry(
                    path="name",
                    message=(f'Plugin name "{data.name}" is not kebab-case; marketplace sync may require kebab-case.'),
                )
            )
        if not data.version:
            warnings.append(
                ValidationWarningEntry(
                    path="version",
                    message="No version specified. Consider semver (e.g., 1.0.0).",
                )
            )
        if not data.description:
            warnings.append(ValidationWarningEntry(path="description", message="No description provided."))
        if not data.author:
            warnings.append(ValidationWarningEntry(path="author", message="No author information provided."))

    return ValidationResult(
        success=len(errors) == 0,
        errors=errors,
        warnings=warnings,
        file_path=absolute_path,
        file_type="plugin",
    )


async def validate_marketplace_manifest(file_path: str) -> ValidationResult:
    errors: list[ValidationErrorEntry] = []
    warnings: list[ValidationWarningEntry] = []
    absolute_path = os.path.abspath(file_path)
    try:
        content = await asyncio.to_thread(
            lambda: open(absolute_path, encoding="utf-8").read(),
        )
    except OSError as e:
        code = get_errno_code(e)
        if code == "ENOENT":
            msg = f"File not found: {absolute_path}"
        elif code == "EISDIR":
            msg = f"Path is not a file: {absolute_path}"
        else:
            msg = f"Failed to read file: {error_message(e)}"
        return ValidationResult(
            success=False,
            errors=[ValidationErrorEntry(path="file", message=msg, code=code)],
            file_path=absolute_path,
            file_type="marketplace",
        )

    try:
        parsed: Any = json.loads(content)
    except json.JSONDecodeError as e:
        return ValidationResult(
            success=False,
            errors=[ValidationErrorEntry(path="json", message=f"Invalid JSON syntax: {e}")],
            file_path=absolute_path,
            file_type="marketplace",
        )

    if isinstance(parsed, dict) and isinstance(parsed.get("plugins"), list):
        for i, plugin in enumerate(parsed["plugins"]):
            if not isinstance(plugin, dict):
                continue
            src = plugin.get("source")
            if isinstance(src, str):
                _check_path_traversal(
                    src,
                    f"plugins[{i}].source",
                    errors,
                    _marketplace_source_hint(src),
                )
            elif isinstance(src, dict) and isinstance(src.get("path"), str):
                _check_path_traversal(src["path"], f"plugins[{i}].source.path", errors)

    try:
        mp = MarketplaceManifestStrict.model_validate(parsed)
    except PydanticValidationError as e:
        errors.extend(_format_pydantic(e))
        return ValidationResult(
            success=False,
            errors=errors,
            warnings=warnings,
            file_path=absolute_path,
            file_type="marketplace",
        )

    if not mp.plugins:
        warnings.append(ValidationWarningEntry(path="plugins", message="Marketplace has no plugins defined"))
    for i, plugin in enumerate(mp.plugins):
        if sum(1 for p in mp.plugins if p.name == plugin.name) > 1:
            errors.append(
                ValidationErrorEntry(
                    path=f"plugins[{i}].name",
                    message=f'Duplicate plugin name "{plugin.name}" found in marketplace',
                )
            )

    manifest_dir = os.path.dirname(absolute_path)
    marketplace_root = (
        os.path.dirname(manifest_dir) if os.path.basename(manifest_dir) == ".claude-plugin" else manifest_dir
    )
    for i, entry in enumerate(mp.plugins):
        if not entry.version or not isinstance(entry.source, str) or not entry.source.startswith("./"):
            continue
        plugin_json_path = os.path.join(
            marketplace_root,
            entry.source,
            ".claude-plugin",
            "plugin.json",
        )
        try:
            raw = await asyncio.to_thread(
                lambda p=plugin_json_path: open(p, encoding="utf-8").read(),
            )
            inner = json.loads(raw)
            mv = inner.get("version") if isinstance(inner, dict) else None
            if isinstance(mv, str) and mv != entry.version:
                warnings.append(
                    ValidationWarningEntry(
                        path=f"plugins[{i}].version",
                        message=(
                            f'Entry declares version "{entry.version}" but '
                            f'{entry.source}/.claude-plugin/plugin.json says "{mv}".'
                        ),
                    )
                )
        except OSError:
            continue

    if not (mp.metadata or {}).get("description"):
        warnings.append(
            ValidationWarningEntry(path="metadata.description", message="No marketplace description provided.")
        )

    return ValidationResult(
        success=len(errors) == 0,
        errors=errors,
        warnings=warnings,
        file_path=absolute_path,
        file_type="marketplace",
    )


def _validate_component_file(
    file_path: str,
    content: str,
    file_type: Literal["skill", "agent", "command"],
) -> ValidationResult:
    errors: list[ValidationErrorEntry] = []
    warnings: list[ValidationWarningEntry] = []
    m = FRONTMATTER_REGEX.match(content)
    if not m:
        warnings.append(
            ValidationWarningEntry(
                path="frontmatter",
                message="No frontmatter block found. Add YAML between --- delimiters.",
            )
        )
        return ValidationResult(
            success=True,
            errors=errors,
            warnings=warnings,
            file_path=file_path,
            file_type=file_type,
        )
    fm_text = m.group(1) or ""
    try:
        parsed = yaml.safe_load(fm_text)
    except yaml.YAMLError as e:
        errors.append(ValidationErrorEntry(path="frontmatter", message=f"YAML frontmatter failed to parse: {e}"))
        return ValidationResult(
            success=False,
            errors=errors,
            warnings=warnings,
            file_path=file_path,
            file_type=file_type,
        )

    if not isinstance(parsed, dict):
        errors.append(ValidationErrorEntry(path="frontmatter", message="Frontmatter must be a YAML mapping."))
        return ValidationResult(
            success=False,
            errors=errors,
            warnings=warnings,
            file_path=file_path,
            file_type=file_type,
        )

    fm = parsed
    d = fm.get("description")
    if d is not None and not isinstance(d, (str, int, float, bool)):
        errors.append(ValidationErrorEntry(path="description", message="description must be a scalar string."))
    elif d is None:
        warnings.append(
            ValidationWarningEntry(path="description", message=f"No description in frontmatter for this {file_type}.")
        )

    name = fm.get("name")
    if name is not None and not isinstance(name, str):
        errors.append(ValidationErrorEntry(path="name", message=f"name must be a string, got {type(name)}."))

    at = fm.get("allowed-tools")
    if at is not None:
        if not isinstance(at, (str, list)):
            errors.append(
                ValidationErrorEntry(
                    path="allowed-tools",
                    message="allowed-tools must be string or array of strings.",
                )
            )
        elif isinstance(at, list) and any(not isinstance(t, str) for t in at):
            errors.append(
                ValidationErrorEntry(path="allowed-tools", message="allowed-tools array must contain only strings.")
            )

    sh = fm.get("shell")
    if sh is not None:
        if not isinstance(sh, str):
            errors.append(ValidationErrorEntry(path="shell", message=f"shell must be a string, got {type(sh)}."))
        elif sh.strip().lower() not in ("bash", "powershell"):
            errors.append(ValidationErrorEntry(path="shell", message=f"shell must be bash or powershell, got {sh!r}."))

    return ValidationResult(
        success=len(errors) == 0,
        errors=errors,
        warnings=warnings,
        file_path=file_path,
        file_type=file_type,
    )


async def validate_hooks_json(file_path: str) -> ValidationResult:
    try:
        content = await asyncio.to_thread(lambda: open(file_path, encoding="utf-8").read())
    except OSError as e:
        if is_enoent(e):
            return ValidationResult(success=True, file_path=file_path, file_type="hooks")
        return ValidationResult(
            success=False,
            errors=[ValidationErrorEntry(path="file", message=f"Failed to read: {error_message(e)}")],
            file_path=file_path,
            file_type="hooks",
        )
    try:
        parsed = json.loads(content)
    except json.JSONDecodeError as e:
        return ValidationResult(
            success=False,
            errors=[
                ValidationErrorEntry(
                    path="json",
                    message=f"Invalid JSON syntax: {e}. At runtime this breaks the entire plugin load.",
                )
            ],
            file_path=file_path,
            file_type="hooks",
        )
    try:
        PluginHooksStrict.model_validate(parsed)
    except PydanticValidationError as e:
        return ValidationResult(
            success=False,
            errors=_format_pydantic(e),
            file_path=file_path,
            file_type="hooks",
        )
    return ValidationResult(success=True, file_path=file_path, file_type="hooks")


async def _collect_markdown(dir_path: str, is_skills_dir: bool) -> list[str]:
    try:
        entries = await asyncio.to_thread(lambda: list(os.scandir(dir_path)))
    except OSError as e:
        code = get_errno_code(e)
        if code in ("ENOENT", "ENOTDIR"):
            return []
        raise
    if is_skills_dir:
        return [os.path.join(dir_path, e.name, "SKILL.md") for e in entries if e.is_dir(follow_symlinks=False)]
    out: list[str] = []
    for e in entries:
        full = os.path.join(dir_path, e.name)
        if e.is_dir(follow_symlinks=False):
            out.extend(await _collect_markdown(full, False))
        elif e.is_file(follow_symlinks=False) and e.name.lower().endswith(".md"):
            out.append(full)
    return out


async def validate_plugin_contents(plugin_dir: str) -> list[ValidationResult]:
    results: list[ValidationResult] = []
    for file_type, sub in (
        ("skill", os.path.join(plugin_dir, "skills")),
        ("agent", os.path.join(plugin_dir, "agents")),
        ("command", os.path.join(plugin_dir, "commands")),
    ):
        files = await _collect_markdown(sub, file_type == "skill")
        for fp in files:
            try:
                content = await asyncio.to_thread(lambda p=fp: open(p, encoding="utf-8").read())
            except OSError as e:
                if is_enoent(e):
                    continue
                results.append(
                    ValidationResult(
                        success=False,
                        errors=[ValidationErrorEntry(path="file", message=f"Failed to read: {error_message(e)}")],
                        file_path=fp,
                        file_type=file_type,  # type: ignore[arg-type]
                    )
                )
                continue
            r = _validate_component_file(fp, content, file_type)  # type: ignore[arg-type]
            if r.errors or r.warnings:
                results.append(r)

    hooks_path = os.path.join(plugin_dir, "hooks", "hooks.json")
    hr = await validate_hooks_json(hooks_path)
    if hr.errors or hr.warnings:
        results.append(hr)
    return results


async def validate_manifest(file_path: str) -> ValidationResult:
    absolute_path = os.path.abspath(file_path)
    try:
        st = await asyncio.to_thread(os.stat, absolute_path)
    except OSError as e:
        if is_enoent(e):
            return ValidationResult(
                success=False,
                errors=[ValidationErrorEntry(path="file", message=f"File not found: {absolute_path}")],
                file_path=absolute_path,
                file_type="plugin",
            )
        raise

    if stat.S_ISDIR(st.st_mode):
        mp_path = os.path.join(absolute_path, ".claude-plugin", "marketplace.json")
        mr = await validate_marketplace_manifest(mp_path)
        if not mr.errors:
            return mr
        if mr.errors[0].code != "ENOENT":
            return mr
        pp = os.path.join(absolute_path, ".claude-plugin", "plugin.json")
        pr = await validate_plugin_manifest(pp)
        if not pr.errors:
            return pr
        if pr.errors[0].code != "ENOENT":
            return pr
        return ValidationResult(
            success=False,
            errors=[
                ValidationErrorEntry(
                    path="directory",
                    message=(
                        "No manifest found. Expected .claude-plugin/marketplace.json or .claude-plugin/plugin.json"
                    ),
                )
            ],
            file_path=absolute_path,
            file_type="plugin",
        )

    mtype = detect_manifest_type(file_path)
    if mtype == "plugin":
        return await validate_plugin_manifest(file_path)
    if mtype == "marketplace":
        return await validate_marketplace_manifest(file_path)

    try:
        content = await asyncio.to_thread(lambda: open(absolute_path, encoding="utf-8").read())
        parsed = safe_parse_json(content)
        if isinstance(parsed, dict) and isinstance(parsed.get("plugins"), list):
            return await validate_marketplace_manifest(file_path)
    except OSError as e:
        if get_errno_code(e) == "ENOENT":
            return ValidationResult(
                success=False,
                errors=[ValidationErrorEntry(path="file", message=f"File not found: {absolute_path}")],
                file_path=absolute_path,
                file_type="plugin",
            )

    return await validate_plugin_manifest(file_path)


__all__ = [
    "FRONTMATTER_REGEX",
    "ValidationResult",
    "ValidationErrorEntry",
    "ValidationWarningEntry",
    "validate_hooks_json",
    "validate_manifest",
    "validate_marketplace_manifest",
    "validate_plugin_contents",
    "validate_plugin_manifest",
]
