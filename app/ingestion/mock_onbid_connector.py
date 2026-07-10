"""Mock Onbid Connector (지시서 §9.3).

실제 온비드 API 연동 없이 샘플 공매 데이터를 반환한다.
ENABLE_MOCK_CONNECTORS=true일 때 사용된다.
"""

from __future__ import annotations

from typing import Any

from app.ingestion.base import BaseConnector

_SAMPLE_ITEMS: list[dict[str, Any]] = [
    {
        "source": "onbid",
        "source_item_id": "ONBID-2026-0001",
        "auction_type": "public_sale",
        "case_number": "ONBID-2026-0001",
        "item_number": "1",
        "category": "apartment",
        "title": "온비드 샘플 아파트",
        "address": "서울특별시 강남구 테헤란로 123",
        "sido": "서울특별시",
        "sigungu": "강남구",
        "appraisal_price": 500000000,
        "minimum_price": 400000000,
        "deposit_price": 40000000,
        "bid_date": "2026-08-01T10:00:00",
        "fail_count": 1,
        "status": "active",
    },
    {
        "source": "onbid",
        "source_item_id": "ONBID-2026-0002",
        "auction_type": "public_sale",
        "case_number": "ONBID-2026-0002",
        "item_number": "1",
        "category": "officetel",
        "title": "온비드 샘플 오피스텔",
        "address": "서울특별시 마포구 월드컵로 45",
        "sido": "서울특별시",
        "sigungu": "마포구",
        "appraisal_price": 250000000,
        "minimum_price": 200000000,
        "deposit_price": 20000000,
        "bid_date": "2026-08-05T10:00:00",
        "fail_count": 0,
        "status": "active",
    },
    {
        "source": "onbid",
        "source_item_id": "ONBID-2026-0003",
        "auction_type": "public_sale",
        "case_number": "ONBID-2026-0003",
        "item_number": "2",
        "category": "commercial",
        "title": "온비드 샘플 상가",
        "address": "부산광역시 해운대구 센텀중앙로 10",
        "sido": "부산광역시",
        "sigungu": "해운대구",
        "appraisal_price": 800000000,
        "minimum_price": 560000000,
        "deposit_price": 56000000,
        "bid_date": "2026-08-10T10:00:00",
        "fail_count": 2,
        "status": "active",
    },
]


class MockOnbidConnector(BaseConnector):
    source = "onbid"

    async def fetch_items(self, **kwargs) -> list[dict[str, Any]]:
        return [dict(item) for item in _SAMPLE_ITEMS]

    async def fetch_detail(self, source_item_id: str) -> dict[str, Any]:
        for item in _SAMPLE_ITEMS:
            if item["source_item_id"] == source_item_id:
                return dict(item)
        raise ValueError(f"Unknown source_item_id: {source_item_id}")
