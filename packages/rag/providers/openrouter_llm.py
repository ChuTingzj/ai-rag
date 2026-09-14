from __future__ import annotations

import httpx

from domain.models import LLMResult, Message

_DEFAULT_TIMEOUT = httpx.Timeout(60.0, connect=10.0)
_MAX_RETRIES = 2


class OpenRouterLLM:
    def __init__(
        self,
        *,
        api_key: str,
        model: str,
        base_url: str = "https://openrouter.ai/api/v1",
        http_referer: str | None = None,
        app_title: str | None = None,
        client: httpx.AsyncClient | None = None,
    ) -> None:
        self._api_key = api_key
        self._default_model = model
        self._base_url = base_url.rstrip("/")
        self._http_referer = http_referer
        self._app_title = app_title
        self._client = client

    def _headers(self) -> dict[str, str]:
        headers: dict[str, str] = {
            "Authorization": f"Bearer {self._api_key}",
            "Content-Type": "application/json",
        }
        if self._http_referer:
            headers["HTTP-Referer"] = self._http_referer
        if self._app_title:
            headers["X-Title"] = self._app_title
        return headers

    async def complete(
        self,
        messages: list[Message],
        *,
        model: str | None = None,
        temperature: float = 0.0,
        max_tokens: int = 2048,
    ) -> LLMResult:
        resolved_model = model or self._default_model
        payload = {
            "model": resolved_model,
            "messages": [m.model_dump() for m in messages],
            "temperature": temperature,
            "max_tokens": max_tokens,
        }
        url = f"{self._base_url}/chat/completions"
        last_exc: Exception | None = None
        for attempt in range(_MAX_RETRIES + 1):
            try:
                if self._client is not None:
                    response = await self._client.post(
                        url, json=payload, headers=self._headers()
                    )
                else:
                    async with httpx.AsyncClient(timeout=_DEFAULT_TIMEOUT) as client:
                        response = await client.post(
                            url, json=payload, headers=self._headers()
                        )
                if response.status_code >= 500 and attempt < _MAX_RETRIES:
                    continue
                response.raise_for_status()
                data = response.json()
                choice = data["choices"][0]["message"]
                usage_raw = data.get("usage") or {}
                usage = {
                    k: int(v)
                    for k, v in usage_raw.items()
                    if isinstance(v, (int, float))
                }
                return LLMResult(
                    content=choice.get("content") or "",
                    model=data.get("model") or resolved_model,
                    usage=usage,
                )
            except httpx.HTTPStatusError:
                raise
            except httpx.HTTPError as exc:
                last_exc = exc
                if attempt >= _MAX_RETRIES:
                    raise
        if last_exc is not None:
            raise last_exc
        raise RuntimeError("OpenRouter request failed without response")
