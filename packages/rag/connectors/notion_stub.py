from __future__ import annotations

from domain.models import ChangePage, RawDocument


class NotionConnector:
    id = "notion"

    async def list_changes(self, cursor: str | None) -> ChangePage:
        _ = cursor
        raise NotImplementedError(
            "Notion connector is not implemented in M1; use Feishu or file upload."
        )

    async def fetch_document(self, external_id: str) -> RawDocument:
        _ = external_id
        raise NotImplementedError(
            "Notion connector is not implemented in M1; use Feishu or file upload."
        )
