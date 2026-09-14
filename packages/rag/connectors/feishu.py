from __future__ import annotations

from typing import Any

import httpx

from domain.models import ChangePage, RawDocument

FEISHU_API_BASE = "https://open.feishu.cn/open-apis"

FEISHU_PAGE_FIXTURE: dict[str, Any] = {
    "node_token": "wikcnFixtureNode",
    "obj_token": "doxcnFixtureDoc",
    "obj_type": "docx",
    "title": "差旅报销政策",
    "edit_time": "1690000000",
    "content": "差旅报销上限为 3000 元。\n二级城市住宿标准见附录。",
}


def map_feishu_page(page: dict[str, Any]) -> RawDocument:
    external_id = str(
        page.get("obj_token") or page.get("document_id") or page.get("node_token") or ""
    )
    if not external_id:
        raise ValueError("Feishu page missing obj_token / document_id / node_token")

    title = str(page.get("title") or "Untitled")
    text = str(page.get("content") or page.get("body") or "")
    node_token = page.get("node_token")
    uri = (
        f"https://feishu.cn/wiki/{node_token}"
        if node_token
        else f"https://feishu.cn/docx/{external_id}"
    )

    return RawDocument(
        external_id=external_id,
        title=title,
        uri=uri,
        mime_type="text/plain",
        content=text.encode("utf-8"),
        meta={
            "edit_time": page.get("edit_time"),
            "obj_type": page.get("obj_type"),
            "node_token": node_token,
        },
    )


class FeishuConnector:
    id = "feishu"

    def __init__(
        self,
        *,
        app_id: str,
        app_secret: str,
        space_id: str,
        client: httpx.AsyncClient | None = None,
    ) -> None:
        self._app_id = app_id
        self._app_secret = app_secret
        self._space_id = space_id
        self._client = client
        self._owns_client = client is None
        self._token: str | None = None

    async def __aenter__(self) -> FeishuConnector:
        if self._client is None:
            self._client = httpx.AsyncClient(base_url=FEISHU_API_BASE, timeout=30.0)
        return self

    async def __aexit__(self, *exc: object) -> None:
        if self._owns_client and self._client is not None:
            await self._client.aclose()
            self._client = None

    def _require_client(self) -> httpx.AsyncClient:
        if self._client is None:
            raise RuntimeError("FeishuConnector client is not initialized; use async with")
        return self._client

    async def _tenant_access_token(self) -> str:
        if self._token:
            return self._token
        client = self._require_client()
        resp = await client.post(
            "/auth/v3/tenant_access_token/internal",
            json={"app_id": self._app_id, "app_secret": self._app_secret},
        )
        resp.raise_for_status()
        body = resp.json()
        if body.get("code") != 0:
            raise RuntimeError(f"Feishu auth failed: {body.get('msg', body)}")
        token = body.get("tenant_access_token")
        if not isinstance(token, str) or not token:
            raise RuntimeError("Feishu auth response missing tenant_access_token")
        self._token = token
        return token

    def _headers(self, token: str) -> dict[str, str]:
        return {"Authorization": f"Bearer {token}"}

    async def list_changes(self, cursor: str | None) -> ChangePage:
        token = await self._tenant_access_token()
        client = self._require_client()
        params: dict[str, str | int] = {"page_size": 50}
        if cursor:
            params["page_token"] = cursor

        resp = await client.get(
            f"/wiki/v2/spaces/{self._space_id}/nodes",
            params=params,
            headers=self._headers(token),
        )
        resp.raise_for_status()
        body = resp.json()
        if body.get("code") != 0:
            raise RuntimeError(f"Feishu list nodes failed: {body.get('msg', body)}")

        data = body.get("data") or {}
        items = data.get("items") or []
        changes: list[dict[str, Any]] = []
        for item in items:
            if not isinstance(item, dict):
                continue
            obj_token = item.get("obj_token")
            if not obj_token:
                continue
            changes.append(
                {
                    "external_id": str(obj_token),
                    "node_token": item.get("node_token"),
                    "obj_type": item.get("obj_type"),
                    "title": item.get("title"),
                    "edit_time": item.get("edit_time") or item.get("node_create_time"),
                }
            )

        next_cursor = data.get("page_token") or data.get("next_page_token")
        return ChangePage(
            changes=changes,
            next_cursor=str(next_cursor) if next_cursor else None,
        )

    async def fetch_document(self, external_id: str) -> RawDocument:
        token = await self._tenant_access_token()
        client = self._require_client()
        resp = await client.get(
            f"/docx/v1/documents/{external_id}/raw_content",
            headers=self._headers(token),
        )
        resp.raise_for_status()
        body = resp.json()
        if body.get("code") != 0:
            raise RuntimeError(f"Feishu fetch document failed: {body.get('msg', body)}")

        data = body.get("data") or {}
        content = data.get("content") if isinstance(data.get("content"), str) else ""
        page_payload: dict[str, Any] = {
            "obj_token": external_id,
            "document_id": external_id,
            "title": data.get("title") or external_id,
            "content": content,
            "obj_type": "docx",
        }
        return map_feishu_page(page_payload)
