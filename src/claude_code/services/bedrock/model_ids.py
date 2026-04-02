"""Bedrock model ID and inference profile string utilities."""

from __future__ import annotations

from typing import Literal

BEDROCK_REGION_PREFIXES = ("us", "eu", "apac", "global")
BedrockRegionPrefix = Literal["us", "eu", "apac", "global"]


def find_first_match(profiles: list[str], substring: str) -> str | None:
    for p in profiles:
        if substring in p:
            return p
    return None


def is_foundation_model(model_id: str) -> bool:
    return model_id.startswith("anthropic.")


def extract_model_id_from_arn(model_id: str) -> str:
    if not model_id.startswith("arn:"):
        return model_id
    idx = model_id.rfind("/")
    if idx == -1:
        return model_id
    return model_id[idx + 1 :]


def get_bedrock_region_prefix(model_id: str) -> BedrockRegionPrefix | None:
    effective = extract_model_id_from_arn(model_id)
    for prefix in BEDROCK_REGION_PREFIXES:
        if effective.startswith(f"{prefix}.anthropic."):
            return prefix  # type: ignore[return-value]
    return None


def apply_bedrock_region_prefix(model_id: str, prefix: BedrockRegionPrefix) -> str:
    existing = get_bedrock_region_prefix(model_id)
    if existing:
        return model_id.replace(f"{existing}.", f"{prefix}.", 1)
    if is_foundation_model(model_id):
        return f"{prefix}.{model_id}"
    return model_id
