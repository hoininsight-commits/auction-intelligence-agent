"""관심 물건 API 테스트 (지시서 §13.6, §7.5)."""

from __future__ import annotations

from datetime import datetime, timedelta, timezone

from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession

from app.models import AuctionItem, User

NOW = datetime.now(timezone.utc).replace(tzinfo=None)


async def _make_item(db_session: AsyncSession, case_number: str = "2024타경4001") -> AuctionItem:
    item = AuctionItem(
        source="court",
        auction_type="real_estate",
        case_number=case_number,
        category="apartment",
        title="관심 물건 테스트",
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
    return item


async def test_add_to_watchlist(
    client: AsyncClient, db_session: AsyncSession, test_user: User
) -> None:
    item = await _make_item(db_session)

    response = await client.post(
        "/api/v1/watchlist",
        json={"user_id": test_user.id, "auction_item_id": item.id, "memo": "입지 좋음"},
    )

    assert response.status_code == 201
    body = response.json()
    assert body["user_id"] == test_user.id
    assert body["auction_item_id"] == item.id
    assert body["memo"] == "입지 좋음"


async def test_add_duplicate_watchlist_is_rejected(
    client: AsyncClient, db_session: AsyncSession, test_user: User
) -> None:
    item = await _make_item(db_session)
    payload = {"user_id": test_user.id, "auction_item_id": item.id, "memo": None}

    first = await client.post("/api/v1/watchlist", json=payload)
    assert first.status_code == 201

    second = await client.post("/api/v1/watchlist", json=payload)
    assert second.status_code == 409


async def test_list_watchlist(
    client: AsyncClient, db_session: AsyncSession, test_user: User
) -> None:
    item1 = await _make_item(db_session, case_number="2024타경4002")
    item2 = await _make_item(db_session, case_number="2024타경4003")

    await client.post(
        "/api/v1/watchlist", json={"user_id": test_user.id, "auction_item_id": item1.id}
    )
    await client.post(
        "/api/v1/watchlist", json={"user_id": test_user.id, "auction_item_id": item2.id}
    )

    response = await client.get("/api/v1/watchlist", params={"user_id": test_user.id})

    assert response.status_code == 200
    body = response.json()
    assert len(body) == 2
    ids = {entry["auction_item_id"] for entry in body}
    assert ids == {item1.id, item2.id}


async def test_delete_watchlist(
    client: AsyncClient, db_session: AsyncSession, test_user: User
) -> None:
    item = await _make_item(db_session, case_number="2024타경4004")
    await client.post(
        "/api/v1/watchlist", json={"user_id": test_user.id, "auction_item_id": item.id}
    )

    response = await client.delete(f"/api/v1/watchlist/{item.id}", params={"user_id": test_user.id})
    assert response.status_code == 204

    listing = await client.get("/api/v1/watchlist", params={"user_id": test_user.id})
    assert listing.json() == []


async def test_delete_watchlist_not_found_returns_404(
    client: AsyncClient, db_session: AsyncSession, test_user: User
) -> None:
    response = await client.delete("/api/v1/watchlist/999999", params={"user_id": test_user.id})

    assert response.status_code == 404
