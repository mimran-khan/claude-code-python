"""Unit tests for ``claude_code.services.api.client``."""

from __future__ import annotations

from unittest.mock import AsyncMock, MagicMock, patch

import httpx
import pytest

from claude_code.services.api.client import (
    AnthropicClient,
    APIRequestError,
    ClientConfig,
    get_anthropic_client,
    is_first_party_anthropic_base_url,
)


@pytest.fixture
def first_party_config() -> ClientConfig:
    return ClientConfig(
        api_key="test-key",
        provider="firstParty",
        base_url="https://api.anthropic.com",
        timeout=30.0,
    )


def test_client_config_defaults() -> None:
    cfg = ClientConfig()
    assert cfg.max_retries == 2
    assert cfg.timeout == 600.0
    assert cfg.provider == "firstParty"


def test_api_request_error_stores_fields() -> None:
    err = APIRequestError(
        "boom",
        status_code=400,
        body_text="{}",
        parsed_json={"a": 1},
    )
    assert err.status_code == 400
    assert err.body_text == "{}"
    assert err.parsed_json == {"a": 1}


def test_anthropic_client_provider_and_base_url_explicit(first_party_config: ClientConfig) -> None:
    client = AnthropicClient(first_party_config)
    assert client.provider == "firstParty"
    assert client.base_url == "https://api.anthropic.com"


@patch.dict("os.environ", {"AWS_REGION": "eu-west-1"}, clear=False)
def test_base_url_bedrock_uses_region() -> None:
    cfg = ClientConfig(provider="bedrock", aws_region=None)
    client = AnthropicClient(cfg)
    assert "bedrock-runtime.eu-west-1.amazonaws.com" in client.base_url


@patch.dict(
    "os.environ",
    {"ANTHROPIC_VERTEX_PROJECT_ID": "p1", "CLOUD_ML_REGION": "us-central1"},
    clear=False,
)
def test_base_url_vertex() -> None:
    cfg = ClientConfig(provider="vertex")
    client = AnthropicClient(cfg)
    assert "us-central1-aiplatform.googleapis.com" in client.base_url
    assert "projects/p1" in client.base_url


@patch.dict("os.environ", {"ANTHROPIC_FOUNDRY_RESOURCE": "myres"}, clear=False)
def test_base_url_foundry() -> None:
    cfg = ClientConfig(provider="foundry")
    client = AnthropicClient(cfg)
    assert client.base_url == "https://myres.services.ai.azure.com"


@patch.dict("os.environ", {"ANTHROPIC_API_URL": "https://custom.example"}, clear=False)
def test_base_url_first_party_env_override() -> None:
    cfg = ClientConfig(provider="firstParty", base_url=None)
    client = AnthropicClient(cfg)
    assert client.base_url == "https://custom.example"


@patch.dict("os.environ", {"ANTHROPIC_API_KEY": "env-key"}, clear=False)
def test_build_headers_includes_api_key_from_env() -> None:
    cfg = ClientConfig(provider="firstParty", api_key=None)
    client = AnthropicClient(cfg)
    headers = client._build_headers()
    assert headers["x-api-key"] == "env-key"
    assert headers["anthropic-version"] == "2023-06-01"


def test_build_headers_merges_default_headers(first_party_config: ClientConfig) -> None:
    first_party_config.default_headers = {"X-Custom": "1"}
    client = AnthropicClient(first_party_config)
    assert client._build_headers()["X-Custom"] == "1"


@pytest.mark.asyncio
async def test_request_json_success_dict(first_party_config: ClientConfig) -> None:
    client = AnthropicClient(first_party_config)
    mock_response = MagicMock()
    mock_response.text = '{"ok": true}'
    mock_response.is_success = True
    mock_client = MagicMock()
    mock_client.request = AsyncMock(return_value=mock_response)
    client._http_client = mock_client

    out = await client.request_json("GET", "/x")
    assert out == {"ok": True}


@pytest.mark.asyncio
async def test_request_json_empty_body_returns_empty_dict(first_party_config: ClientConfig) -> None:
    client = AnthropicClient(first_party_config)
    mock_response = MagicMock()
    mock_response.text = ""
    mock_response.is_success = True
    mock_client = MagicMock()
    mock_client.request = AsyncMock(return_value=mock_response)
    client._http_client = mock_client

    assert await client.request_json("GET", "/x") == {}


@pytest.mark.asyncio
async def test_request_json_http_error_parses_error_message(first_party_config: ClientConfig) -> None:
    client = AnthropicClient(first_party_config)
    mock_response = MagicMock()
    mock_response.text = '{"error": {"message": "nope"}}'
    mock_response.status_code = 422
    mock_response.is_success = False
    mock_client = MagicMock()
    mock_client.request = AsyncMock(return_value=mock_response)
    client._http_client = mock_client

    with pytest.raises(APIRequestError) as ei:
        await client.request_json("POST", "/v1/messages")
    assert ei.value.status_code == 422
    assert "nope" in str(ei.value)


@pytest.mark.asyncio
async def test_request_json_request_error_wraps(first_party_config: ClientConfig) -> None:
    client = AnthropicClient(first_party_config)
    mock_client = MagicMock()
    mock_client.request = AsyncMock(side_effect=httpx.RequestError("fail", request=MagicMock()))
    client._http_client = mock_client

    with pytest.raises(APIRequestError) as ei:
        await client.request_json("GET", "/")
    assert ei.value.status_code == 0


@pytest.mark.asyncio
async def test_messages_create_non_dict_raises(first_party_config: ClientConfig) -> None:
    client = AnthropicClient(first_party_config)
    with (
        patch.object(client, "request_json", new_callable=AsyncMock, return_value=[]),
        pytest.raises(APIRequestError, match="Unexpected non-object"),
    ):
        await client.messages_create("m", 10, [])


@pytest.mark.asyncio
async def test_messages_create_success(first_party_config: ClientConfig) -> None:
    client = AnthropicClient(first_party_config)
    with patch.object(client, "request_json", new_callable=AsyncMock, return_value={"id": "1"}):
        out = await client.messages_create("m", 10, [{"role": "user", "content": "hi"}])
    assert out["id"] == "1"


@pytest.mark.asyncio
async def test_close_closes_http_client(first_party_config: ClientConfig) -> None:
    client = AnthropicClient(first_party_config)
    mock_http = MagicMock()
    mock_http.aclose = AsyncMock()
    client._http_client = mock_http
    await client.close()
    mock_http.aclose.assert_awaited_once()
    assert client._http_client is None


@pytest.mark.parametrize(
    "provider",
    ["bedrock", "vertex", "foundry", "firstParty"],
)
@pytest.mark.asyncio
async def test_get_anthropic_client_respects_detected_provider(provider: str) -> None:
    with patch("claude_code.services.api.client._get_provider", return_value=provider):
        client = await get_anthropic_client(api_key="k")
    assert client.config.provider == provider


def test_get_provider_bedrock_when_env_set() -> None:
    with (
        patch.dict("os.environ", {"CLAUDE_CODE_USE_BEDROCK": "1"}),
        patch("claude_code.utils.env_utils.is_env_truthy", return_value=True),
    ):
        from claude_code.services.api.client import _get_provider

        assert _get_provider() == "bedrock"


def test_get_provider_defaults_first_party() -> None:
    with (
        patch.dict("os.environ", {}, clear=True),
        patch("claude_code.utils.env_utils.is_env_truthy", return_value=False),
    ):
        from claude_code.services.api.client import _get_provider

        assert _get_provider() == "firstParty"


def test_is_first_party_anthropic_base_url() -> None:
    assert is_first_party_anthropic_base_url("https://api.anthropic.com/v1") is True
    assert is_first_party_anthropic_base_url("https://api.ant.dev/x") is True
    assert is_first_party_anthropic_base_url("https://example.com") is False
