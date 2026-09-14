from __future__ import annotations

from connectors.feishu import FEISHU_PAGE_FIXTURE, map_feishu_page


def test_feishu_page_to_raw_document() -> None:
    raw = map_feishu_page(FEISHU_PAGE_FIXTURE)
    assert raw.title
    assert raw.text
    assert raw.external_id
