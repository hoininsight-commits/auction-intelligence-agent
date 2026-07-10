"""경매 물건 검색/상세 API 테스트 (지시서 §13.2, §13.3)."""

from __future__ import annotations

from datetime import datetime, timedelta, timezone

from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession

from app.models import AuctionItem

NOW = datetime.now(timezone.utc).replace(tzinfo=None)


def _make_item(**overrides) -> AuctionItem:
    defaults = dict(
        source="court",
        auction_type="real_estate",
        case_number="2024타경0000",
        category="apartment",
        title="테스트 물건",
        address="서울특별시 강남구",
        sido="서울특별시",
        sigungu="강남구",
        appraisal_price=1_000_000_000,
        minimum_price=800_000_000,
        bid_date=NOW + timedelta(days=10),
        fail_count=0,
        status="active",
    )
    defaults.update(overrides)
    return AuctionItem(**defaults)


async def _seed_items(db_session: AsyncSession) -> list[AuctionItem]:
    items = [
        _make_item(
            case_number="2024타경1001",
            category="apartment",
            sido="서울특별시",
            sigungu="강남구",
            minimum_price=500_000_000,
            appraisal_price=700_000_000,
        ),
        _make_item(
            case_number="2024타경1002",
            category="villa",
            sido="경기도",
            sigungu="수원시",
            minimum_price=200_000_000,
            appraisal_price=300_000_000,
        ),
        _make_item(
            case_number="2024타경1003",
            category="commercial",
            sido="부산광역시",
            sigungu="해운대구",
            minimum_price=900_000_000,
            appraisal_price=1_200_000_000,
        ),
    ]
    db_session.add_all(items)
    await db_session.commit()
    for item in items:
        await db_session.refresh(item)
    return items


# ---------------------------------------------------------------------------
# §13.2 검색 API 테스트
# ---------------------------------------------------------------------------


async def test_search_default_list(client: AsyncClient, db_session: AsyncSession) -> None:
    await _seed_items(db_session)

    response = await client.get("/api/v1/auction-items")

    assert response.status_code == 200
    body = response.json()
    assert len(body["items"]) == 3
    assert body["pagination"]["total"] == 3
    assert body["pagination"]["page"] == 1


async def test_search_filter_by_region(client: AsyncClient, db_session: AsyncSession) -> None:
    await _seed_items(db_session)

    response = await client.get("/api/v1/auction-items", params={"sido": "경기도"})

    assert response.status_code == 200
    body = response.json()
    assert len(body["items"]) == 1
    assert body["items"][0]["sido"] == "경기도"


async def test_search_filter_by_category(client: AsyncClient, db_session: AsyncSession) -> None:
    await _seed_items(db_session)

    response = await client.get("/api/v1/auction-items", params={"category": "villa"})

    assert response.status_code == 200
    body = response.json()
    assert len(body["items"]) == 1
    assert body["items"][0]["category"] == "villa"


async def test_search_filter_by_price_range(client: AsyncClient, db_session: AsyncSession) -> None:
    await _seed_items(db_session)

    # min_price/max_price는 AuctionItem.minimum_price 컬럼에 적용된다 (repository 구현 기준).
    response = await client.get(
        "/api/v1/auction-items",
        params={"min_price": 400_000_000, "max_price": 600_000_000},
    )

    assert response.status_code == 200
    body = response.json()
    assert len(body["items"]) == 1
    assert body["items"][0]["minimum_price"] == 500_000_000


async def test_search_pagination(client: AsyncClient, db_session: AsyncSession) -> None:
    items = [
        _make_item(case_number=f"2024타경{2000 + i}", minimum_price=100_000_000 * (i + 1))
        for i in range(5)
    ]
    db_session.add_all(items)
    await db_session.commit()

    response = await client.get(
        "/api/v1/auction-items", params={"page": 2, "limit": 2, "sort": "minimum_price_asc"}
    )

    assert response.status_code == 200
    body = response.json()
    assert len(body["items"]) == 2
    assert body["pagination"] == {"page": 2, "limit": 2, "total": 5, "total_pages": 3}
    # minimum_price_asc 정렬 + page 2/limit 2 => 3번째, 4번째로 싼 물건이 나온다.
    assert body["items"][0]["minimum_price"] == 300_000_000
    assert body["items"][1]["minimum_price"] == 400_000_000


async def test_search_sort_by_minimum_price_desc(
    client: AsyncClient, db_session: AsyncSession
) -> None:
    await _seed_items(db_session)

    response = await client.get("/api/v1/auction-items", params={"sort": "minimum_price_desc"})

    assert response.status_code == 200
    prices = [item["minimum_price"] for item in response.json()["items"]]
    assert prices == sorted(prices, reverse=True)


# ---------------------------------------------------------------------------
# §13.3 상세 API 테스트
# ---------------------------------------------------------------------------


async def test_get_detail_existing_item(client: AsyncClient, db_session: AsyncSession) -> None:
    items = await _seed_items(db_session)
    target = items[0]

    response = await client.get(f"/api/v1/auction-items/{target.id}")

    assert response.status_code == 200
    body = response.json()
    assert body["id"] == target.id
    assert body["case_number"] == target.case_number
    assert body["disclaimer"]


async def test_get_detail_not_found_returns_404(
    client: AsyncClient, db_session: AsyncSession
) -> None:
    response = await client.get("/api/v1/auction-items/999999")

    assert response.status_code == 404
