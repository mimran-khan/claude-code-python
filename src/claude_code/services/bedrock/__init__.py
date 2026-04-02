"""
Amazon Bedrock helpers (model IDs, optional AWS clients).

Migrated from: utils/model/bedrock.ts
"""

from .client import get_inference_profile_backing_model, list_inference_profile_ids_anthropic
from .model_ids import (
    BEDROCK_REGION_PREFIXES,
    BedrockRegionPrefix,
    apply_bedrock_region_prefix,
    extract_model_id_from_arn,
    find_first_match,
    get_bedrock_region_prefix,
    is_foundation_model,
)

__all__ = [
    "BEDROCK_REGION_PREFIXES",
    "BedrockRegionPrefix",
    "apply_bedrock_region_prefix",
    "extract_model_id_from_arn",
    "find_first_match",
    "get_bedrock_region_prefix",
    "is_foundation_model",
    "get_inference_profile_backing_model",
    "list_inference_profile_ids_anthropic",
]
