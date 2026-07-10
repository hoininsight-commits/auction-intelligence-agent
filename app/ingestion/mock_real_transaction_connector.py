"""Mock Real Transaction Connector (지시서 §9.4).

실제 국토부 실거래가 API 연동 없이 샘플 실거래가 데이터를 반환한다.
ENABLE_MOCK_CONNECTORS=true일 때 사용된다.
"""
from __future__ import annotations

from typing import Any

from app.ingestion.base import BaseConnector

_SAMPLE_ITEMS: list[dict[str, Any]] = [
    {
        "property_type": "apartment",
        "address": "서울특별시 강남구 테헤란로 123",
        "sido": "서울특별시",
        "sigungu": "강남구",
        "eupmyeondong": "역삼동",
        "complex_name": "샘플아파트",
        "exclusive_area": 84.5,
        "deal_price": 470000000,
        "deal_year": 2026,
        "deal_month": 6,
        "deal_day": 10,
        "floor_info": "10",
        "build_year": 2015,
        "source": "molit_mock",
    },
    {
        "property_type": "apartment",
        "address": "서울특별시 강남구 테헤란로 130",
        "sido": "서울특별시",
        "sigungu": "강남구",
        "eupmyeondong": "역삼동",
        "complex_name": "샘플아파트",
        "exclusive_area": 84.5,
        "deal_price": 465000000,
        "deal_year": 2026,
        "deal_month": 5,
        "deal_day": 22,
        "floor_info": "5",
        "build_year": 2015,
        "source": "molit_mock",
    },
    {
        "property_type": "officetel",
        "address": "서울특별시 마포구 월드컵로 45",
        "sido": "서울특별시",
        "sigungu": "마포구",
        "eupmyeondong": "성산동",
        "complex_name": "샘플오피스텔",
        "exclusive_area": 45.2,
        "deal_price": 230000000,
        "deal_year": 2026,
        "deal_month": 6,
        "deal_day": 1,
        "floor_info": "8",
        "build_year": 2018,
        "source": "molit_mock",
    },
]


class MockRealTransactionConnector(BaseConnector):
    source = "molit_mock"

    async def fetch_items(self, **kwargs) -> list[dict[str, Any]]:
        return [dict(item) for item in _SAMPLE_ITEMS]

    async def fetch_detail(self, source_item_id: str) -> dict[str, Any]:
        # 실거래가 데이터는 개별 상세 조회 개념이 없으므로 인덱스 기반으로 조회한다.
        try:
            idx = int(source_item_id)
            return dict(_SAMPLE_ITEMS[idx])
        except (ValueError, IndexError) as exc:
            raise ValueError(f"Unknown source_item_id: {source_item_id}") from exc
