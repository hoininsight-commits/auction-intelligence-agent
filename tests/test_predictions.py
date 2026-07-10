"""참고 낙찰가 예측 API 테스트 (지시서 §13.4, §8)."""
from __future__ import annotations

from datetime import datetime, timedelta, timezone

from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession

from app.models import AuctionItem

NOW = datetime.now(timezone.utc).replace(tzinfo=None)


async def test_predict_price_from_appraisal_price(client: AsyncClient, db_session: AsyncSession) -> None:
    """유사 낙찰 사례/최저가 배수 데이터가 없으면 감정가 × 카테고리 기본 낙찰가율로 계산한다 (§8.2)."""
    item = AuctionItem(
        source="court",
        auction_type="real_estate",
        case_number="2024타경3001",
        category="apartment",
        title="감정가 기반 예측 테스트",
        address="서울특별시 강남구",
        sido="서울특별시",
        sigungu="강남구",
        appraisal_price=1_000_000_000,
        minimum_price=800_000_000,
        bid_date=NOW + timedelta(days=10),
        fail_count=0,
        status="active",
    )
    db_session.add(item)
    await db_session.commit()
    await db_session.refresh(item)

    response = await client.post(f"/api/v1/auction-items/{item.id}/predict-price")

    assert response.status_code == 200
    body = response.json()
    assert body["auction_item_id"] == item.id
    assert body["predicted_price_mid"] > 0
    # 감정가 기반(카테고리 기본 낙찰가율 84%, 지시서 §8.3)이었음을 explanation에서 확인.
    assert any("감정가" in msg or "낙찰가율" in msg for msg in body["explanation"])
    assert body["predicted_rate_mid"] is not None
    assert body["confidence"] in {"low", "medium", "high"}
    assert body["model_version"] == "rule-v1"


async def test_predict_price_falls_back_to_minimum_price(
    client: AsyncClient, db_session: AsyncSession
) -> None:
    """감정가가 없으면 최저가 기준으로 fallback 계산한다 (§8.2 극단적 fallback)."""
    item = AuctionItem(
        source="court",
        auction_type="real_estate",
        case_number="2024타경3002",
        category="apartment",
        title="최저가 fallback 테스트",
        address="서울특별시 강남구",
        sido="서울특별시",
        sigungu="강남구",
        appraisal_price=None,
        minimum_price=500_000_000,
        bid_date=NOW + timedelta(days=10),
        fail_count=0,
        status="active",
    )
    db_session.add(item)
    await db_session.commit()
    await db_session.refresh(item)

    response = await client.post(f"/api/v1/auction-items/{item.id}/predict-price")

    assert response.status_code == 200
    body = response.json()
    assert any("최저가" in msg for msg in body["explanation"])
    # 감정가가 없으므로 predicted_rate_*는 계산할 수 없다 (_compute_rates 구현 기준).
    assert body["predicted_rate_low"] is None
    assert body["predicted_rate_mid"] is None
    assert body["predicted_rate_high"] is None
    assert body["predicted_price_mid"] > 0


async def test_predict_price_includes_disclaimer(client: AsyncClient, db_session: AsyncSession) -> None:
    item = AuctionItem(
        source="court",
        auction_type="real_estate",
        case_number="2024타경3003",
        category="villa",
        title="고지문 확인 테스트",
        address="경기도 수원시",
        sido="경기도",
        sigungu="수원시",
        appraisal_price=300_000_000,
        minimum_price=240_000_000,
        bid_date=NOW + timedelta(days=10),
        fail_count=1,
        status="active",
    )
    db_session.add(item)
    await db_session.commit()
    await db_session.refresh(item)

    response = await client.post(f"/api/v1/auction-items/{item.id}/predict-price")

    assert response.status_code == 200
    body = response.json()
    assert body["disclaimer"]
    assert "참고" in body["disclaimer"]


async def test_predict_price_not_found_returns_404(client: AsyncClient) -> None:
    response = await client.post("/api/v1/auction-items/999999/predict-price")

    assert response.status_code == 404
