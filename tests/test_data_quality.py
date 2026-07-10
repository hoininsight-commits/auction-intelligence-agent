"""데이터 품질 API 테스트 (지시서 §13.8, §7.8, §10)."""

from __future__ import annotations

from datetime import datetime, timedelta, timezone

from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession

from app.models import AuctionItem

NOW = datetime.now(timezone.utc).replace(tzinfo=None)


def _base_item(**overrides) -> AuctionItem:
    defaults = dict(
        source="court",
        auction_type="real_estate",
        case_number="2024타경5000",
        category="apartment",
        title="데이터 품질 테스트",
        address="서울특별시 강남구",
        sido="서울특별시",
        sigungu="강남구",
        latitude=37.5,
        longitude=127.0,
        appraisal_price=1_000_000_000,
        minimum_price=800_000_000,
        bid_date=NOW + timedelta(days=10),
        fail_count=0,
        status="active",
    )
    defaults.update(overrides)
    return AuctionItem(**defaults)


async def test_data_quality_missing_appraisal_price_count(
    client: AsyncClient, db_session: AsyncSession
) -> None:
    ok_item = _base_item(case_number="2024타경5001")
    missing_appraisal = _base_item(case_number="2024타경5002", appraisal_price=None)
    db_session.add_all([ok_item, missing_appraisal])
    await db_session.commit()

    response = await client.get("/api/v1/admin/data-quality/summary")

    assert response.status_code == 200
    body = response.json()
    assert body["total_items"] == 2
    assert body["missing_appraisal_price"] == 1


async def test_data_quality_missing_coordinates_count(
    client: AsyncClient, db_session: AsyncSession
) -> None:
    ok_item = _base_item(case_number="2024타경5003")
    missing_coords = _base_item(case_number="2024타경5004", latitude=None, longitude=None)
    db_session.add_all([ok_item, missing_coords])
    await db_session.commit()

    response = await client.get("/api/v1/admin/data-quality/summary")

    assert response.status_code == 200
    body = response.json()
    assert body["missing_coordinates"] == 1


async def test_data_quality_past_bid_date_active_status_count(
    client: AsyncClient, db_session: AsyncSession
) -> None:
    future_active = _base_item(
        case_number="2024타경5005", bid_date=NOW + timedelta(days=5), status="active"
    )
    past_active = _base_item(
        case_number="2024타경5006", bid_date=NOW - timedelta(days=5), status="active"
    )
    past_closed = _base_item(
        case_number="2024타경5007", bid_date=NOW - timedelta(days=5), status="sold"
    )
    db_session.add_all([future_active, past_active, past_closed])
    await db_session.commit()

    response = await client.get("/api/v1/admin/data-quality/summary")

    assert response.status_code == 200
    body = response.json()
    # 입찰일이 과거인데도 상태가 여전히 active인 물건만 카운트되어야 한다.
    assert body["past_bid_date_active_status"] == 1
