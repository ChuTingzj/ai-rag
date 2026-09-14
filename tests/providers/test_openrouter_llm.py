import pytest

from domain.models import Message
from providers.openrouter_llm import OpenRouterLLM


@pytest.mark.asyncio
async def test_openrouter_complete(httpx_mock):
    httpx_mock.add_response(
        json={
            "choices": [{"message": {"content": "hello [E1]"}}],
            "usage": {"prompt_tokens": 1, "completion_tokens": 1},
        }
    )
    llm = OpenRouterLLM(
        api_key="t",
        model="openai/gpt-4.1-mini",
        base_url="https://openrouter.ai/api/v1",
    )
    result = await llm.complete([Message(role="user", content="hi")])
    assert "hello" in result.text


@pytest.mark.asyncio
async def test_openrouter_sends_auth_header(httpx_mock):
    httpx_mock.add_response(
        json={
            "choices": [{"message": {"content": "ok"}}],
            "usage": {},
        }
    )
    llm = OpenRouterLLM(
        api_key="secret-key",
        model="openai/gpt-4.1-mini",
        base_url="https://openrouter.ai/api/v1",
    )
    await llm.complete([Message(role="user", content="hi")])
    request = httpx_mock.get_requests()[0]
    assert request.headers["authorization"] == "Bearer secret-key"
