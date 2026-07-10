"""법원 경매정보 Connector.

크롤링 구현 금지(지시서 §1, §9.1) — 법적 리스크가 있는 스크레이핑은 이 프로젝트 범위 밖이다.
공식 API가 제공되지 않는 한 이 Connector는 인터페이스만 존재하며 실제 fetch 로직은 구현하지 않는다.
"""

from __future__ import annotations

from typing import Any

from app.ingestion.base import BaseConnector


class CourtAuctionConnector(BaseConnector):
    """법원(대법원) 경매정보 Connector 스텁.

    크롤링은 구현하지 않는다. 공식 Open API가 제공될 경우에만 구현 가능하다.
    """

    source = "court"

    async def fetch_items(self, **kwargs) -> list[dict[str, Any]]:
        raise NotImplementedError(
            "법원 경매정보는 크롤링을 통해서만 수집 가능하며, 이 프로젝트는 크롤링을 구현하지 않는다. "
            "공식 API가 제공되기 전까지 CourtAuctionConnector는 사용할 수 없다."
        )

    async def fetch_detail(self, source_item_id: str) -> dict[str, Any]:
        raise NotImplementedError(
            "법원 경매정보는 크롤링을 통해서만 수집 가능하며, 이 프로젝트는 크롤링을 구현하지 않는다."
        )
