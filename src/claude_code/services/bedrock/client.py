"""
Optional Bedrock control-plane calls (requires boto3).

Migrated from: utils/model/bedrock.ts (client operations).
"""

from __future__ import annotations

import asyncio
import os
from typing import Any

from .model_ids import extract_model_id_from_arn


def _aws_region() -> str:
    return os.environ.get("AWS_REGION") or os.environ.get("AWS_DEFAULT_REGION") or "us-east-1"


def _require_boto3() -> Any:
    try:
        import boto3
    except ImportError as exc:
        raise RuntimeError("boto3 is required for Bedrock client operations") from exc
    return boto3


async def list_inference_profile_ids_anthropic() -> list[str]:
    """List SYSTEM_DEFINED inference profile IDs containing 'anthropic'."""

    def _sync() -> list[str]:
        boto3 = _require_boto3()
        client = boto3.client("bedrock", region_name=_aws_region())
        profiles: list[str] = []
        token: str | None = None
        while True:
            kwargs: dict[str, Any] = {"typeEquals": "SYSTEM_DEFINED"}
            if token:
                kwargs["nextToken"] = token
            resp = client.list_inference_profiles(**kwargs)
            for s in resp.get("inferenceProfileSummaries", []) or []:
                pid = s.get("inferenceProfileId")
                if isinstance(pid, str) and "anthropic" in pid:
                    profiles.append(pid)
            token = resp.get("nextToken")
            if not token:
                break
        return profiles

    return await asyncio.to_thread(_sync)


async def get_inference_profile_backing_model(profile_id: str) -> str | None:
    def _sync() -> str | None:
        boto3 = _require_boto3()
        client = boto3.client("bedrock", region_name=_aws_region())
        try:
            resp = client.get_inference_profile(inferenceProfileIdentifier=profile_id)
        except Exception:
            return None
        models = resp.get("models") or []
        if not models:
            return None
        arn = models[0].get("modelArn")
        if not isinstance(arn, str):
            return None
        return extract_model_id_from_arn(arn)

    return await asyncio.to_thread(_sync)
