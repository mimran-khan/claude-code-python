"""
Anthropic API client.

Client creation and configuration for different providers.

Migrated from: services/api/client.ts (390 lines)
"""

from __future__ import annotations

import json
import os
from dataclasses import dataclass, field
from typing import Any, Literal

import httpx

# Provider types
APIProvider = Literal["firstParty", "bedrock", "vertex", "foundry"]


class APIRequestError(Exception):
    """HTTP API failure with parsed body when JSON."""

    def __init__(
        self,
        message: str,
        *,
        status_code: int,
        body_text: str,
        parsed_json: dict[str, Any] | list[Any] | None = None,
    ) -> None:
        super().__init__(message)
        self.status_code = status_code
        self.body_text = body_text
        self.parsed_json = parsed_json


@dataclass
class ClientConfig:
    """Configuration for the Anthropic client."""

    api_key: str | None = None
    base_url: str | None = None
    max_retries: int = 2
    timeout: float = 600.0
    model: str | None = None
    provider: APIProvider = "firstParty"

    # Headers
    default_headers: dict[str, str] = field(default_factory=dict)

    # AWS Bedrock specific
    aws_region: str | None = None
    aws_access_key_id: str | None = None
    aws_secret_access_key: str | None = None

    # GCP Vertex specific
    vertex_project_id: str | None = None
    vertex_region: str | None = None

    # Azure Foundry specific
    foundry_resource: str | None = None
    foundry_api_key: str | None = None


class AnthropicClient:
    """
    Anthropic API client wrapper.

    Supports multiple providers:
    - Direct Anthropic API
    - AWS Bedrock
    - Google Vertex AI
    - Azure Foundry
    """

    def __init__(self, config: ClientConfig):
        self.config = config
        self._http_client: httpx.AsyncClient | None = None

    @property
    def provider(self) -> APIProvider:
        """Get the API provider."""
        return self.config.provider

    @property
    def base_url(self) -> str:
        """Get the base URL for API calls."""
        if self.config.base_url:
            return self.config.base_url

        if self.provider == "bedrock":
            region = self.config.aws_region or os.getenv("AWS_REGION", "us-east-1")
            return f"https://bedrock-runtime.{region}.amazonaws.com"

        if self.provider == "vertex":
            project = self.config.vertex_project_id or os.getenv("ANTHROPIC_VERTEX_PROJECT_ID", "")
            region = self.config.vertex_region or os.getenv("CLOUD_ML_REGION", "us-east5")
            return f"https://{region}-aiplatform.googleapis.com/v1/projects/{project}"

        if self.provider == "foundry":
            resource = self.config.foundry_resource or os.getenv("ANTHROPIC_FOUNDRY_RESOURCE", "")
            return f"https://{resource}.services.ai.azure.com"

        return os.getenv("ANTHROPIC_API_URL", "https://api.anthropic.com")

    async def _get_http_client(self) -> httpx.AsyncClient:
        """Get or create the HTTP client."""
        if self._http_client is None:
            self._http_client = httpx.AsyncClient(
                base_url=self.base_url,
                timeout=httpx.Timeout(self.config.timeout),
                headers=self._build_headers(),
            )
        return self._http_client

    def _build_headers(self) -> dict[str, str]:
        """Build request headers."""
        headers = {
            "Content-Type": "application/json",
            "anthropic-version": "2023-06-01",
            "x-app": "cli",
            **self.config.default_headers,
        }

        # Add API key for first-party
        if self.provider == "firstParty":
            api_key = self.config.api_key or os.getenv("ANTHROPIC_API_KEY")
            if api_key:
                headers["x-api-key"] = api_key

        return headers

    async def request_json(
        self,
        method: str,
        path: str,
        *,
        json_body: dict[str, Any] | list[Any] | None = None,
        params: dict[str, Any] | None = None,
        headers: dict[str, str] | None = None,
    ) -> dict[str, Any] | list[Any]:
        """
        Perform an HTTP call and parse JSON.

        Raises:
            APIRequestError: On non-success status or invalid JSON.
        """
        client = await self._get_http_client()
        extra = headers or {}
        try:
            response = await client.request(
                method.upper(),
                path,
                json=json_body,
                params=params,
                headers=extra if extra else None,
            )
        except httpx.RequestError as e:
            raise APIRequestError(
                f"Request failed: {e}",
                status_code=0,
                body_text=str(e),
                parsed_json=None,
            ) from e

        text = response.text
        parsed: dict[str, Any] | list[Any] | None = None
        if text:
            try:
                loaded = json.loads(text)
                if isinstance(loaded, (dict, list)):
                    parsed = loaded
            except json.JSONDecodeError:
                parsed = None

        if not response.is_success:
            msg = "HTTP error"
            if isinstance(parsed, dict):
                err = parsed.get("error")
                if isinstance(err, dict):
                    msg = str(err.get("message", err))
                elif isinstance(err, str):
                    msg = err
            raise APIRequestError(
                msg,
                status_code=response.status_code,
                body_text=text[:8000],
                parsed_json=parsed,
            )

        if parsed is None:
            return {}
        if isinstance(parsed, dict):
            return parsed
        return parsed

    async def messages_create(
        self,
        model: str,
        max_tokens: int,
        messages: list[dict[str, Any]],
        system: str | None = None,
        tools: list[dict[str, Any]] | None = None,
        stream: bool = False,
        **kwargs,
    ) -> dict[str, Any]:
        """
        Create a message (non-streaming).

        Args:
            model: Model name
            max_tokens: Maximum output tokens
            messages: Conversation messages
            system: Optional system prompt
            tools: Optional tool definitions
            stream: Whether to stream
            **kwargs: Additional parameters

        Returns:
            API response
        """
        await self._get_http_client()

        payload = {
            "model": model,
            "max_tokens": max_tokens,
            "messages": messages,
            **kwargs,
        }

        if system:
            payload["system"] = system

        if tools:
            payload["tools"] = tools

        try:
            result = await self.request_json("POST", "/v1/messages", json_body=payload)
        except APIRequestError:
            raise
        if not isinstance(result, dict):
            raise APIRequestError(
                "Unexpected non-object JSON from /v1/messages",
                status_code=500,
                body_text=str(result)[:2000],
                parsed_json=None,
            )
        return result

    async def messages_stream(
        self,
        model: str,
        max_tokens: int,
        messages: list[dict[str, Any]],
        system: str | None = None,
        tools: list[dict[str, Any]] | None = None,
        **kwargs,
    ):
        """
        Create a streaming message.

        Args:
            model: Model name
            max_tokens: Maximum output tokens
            messages: Conversation messages
            system: Optional system prompt
            tools: Optional tool definitions
            **kwargs: Additional parameters

        Yields:
            Stream events
        """
        client = await self._get_http_client()

        payload = {
            "model": model,
            "max_tokens": max_tokens,
            "messages": messages,
            "stream": True,
            **kwargs,
        }

        if system:
            payload["system"] = system

        if tools:
            payload["tools"] = tools

        async with client.stream(
            "POST",
            "/v1/messages",
            json=payload,
        ) as response:
            response.raise_for_status()
            async for line in response.aiter_lines():
                if line.startswith("data: "):
                    data = json.loads(line[6:])
                    yield data

    async def close(self):
        """Close the HTTP client."""
        if self._http_client:
            await self._http_client.aclose()
            self._http_client = None


def _get_provider() -> APIProvider:
    """Detect the API provider from environment."""
    from ...utils.env_utils import is_env_truthy

    if is_env_truthy(os.getenv("CLAUDE_CODE_USE_BEDROCK")):
        return "bedrock"

    if is_env_truthy(os.getenv("CLAUDE_CODE_USE_VERTEX")):
        return "vertex"

    if is_env_truthy(os.getenv("CLAUDE_CODE_USE_FOUNDRY")):
        return "foundry"

    return "firstParty"


async def get_anthropic_client(
    api_key: str | None = None,
    max_retries: int = 2,
    model: str | None = None,
    **kwargs,
) -> AnthropicClient:
    """
    Create an Anthropic client.

    Args:
        api_key: Optional API key (defaults to env var)
        max_retries: Maximum retry attempts
        model: Optional model name
        **kwargs: Additional config options

    Returns:
        Configured AnthropicClient
    """
    provider = _get_provider()

    config = ClientConfig(
        api_key=api_key,
        max_retries=max_retries,
        model=model,
        provider=provider,
        **kwargs,
    )

    return AnthropicClient(config)


def is_first_party_anthropic_base_url(url: str) -> bool:
    """Check if URL is first-party Anthropic."""
    anthropic_urls = [
        "api.anthropic.com",
        "api.ant.dev",
    ]
    return any(base in url for base in anthropic_urls)
