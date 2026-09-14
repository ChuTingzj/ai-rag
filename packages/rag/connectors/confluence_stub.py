from __future__ import annotations

from domain.models import ChangePage, RawDocument


class ConfluenceConnector:
    id = "confluence"

    async def list_changes(self, cursor: str | None) -> ChangePage:
        _ = cursor
        raise NotImplementedError(
            "Confluence connector is not implemented in M1; use Feishu or file upload."
        )

    async def fetch_document(self, external_id: str) -> RawDocument:
        _ = external_id
        raise NotImplementedError(
            "Confluence connector is not implemented in M1; use Feishu or file upload."
        )
