"""저장 검색 API 테스트 (지시서 §13.7, §7.6)."""

from __future__ import annotations

from httpx import AsyncClient

from app.models import User


async def test_create_saved_search(client: AsyncClient, test_user: User) -> None:
    payload = {
        "user_id": test_user.id,
        "name": "강남 아파트 3억 이하",
        "filters": {"sido": "서울특별시", "sigungu": "강남구", "max_price": 300_000_000},
        "alert_enabled": True,
    }

    response = await client.post("/api/v1/saved-searches", json=payload)

    assert response.status_code == 201
    body = response.json()
    assert body["user_id"] == test_user.id
    assert body["name"] == payload["name"]
    assert body["filters"] == payload["filters"]
    assert body["alert_enabled"] is True
    assert "id" in body


async def test_list_saved_searches(client: AsyncClient, test_user: User) -> None:
    await client.post(
        "/api/v1/saved-searches",
        json={"user_id": test_user.id, "name": "검색1", "filters": {"category": "apartment"}},
    )
    await client.post(
        "/api/v1/saved-searches",
        json={"user_id": test_user.id, "name": "검색2", "filters": {"category": "villa"}},
    )

    response = await client.get("/api/v1/saved-searches", params={"user_id": test_user.id})

    assert response.status_code == 200
    body = response.json()
    assert len(body) == 2
    names = {entry["name"] for entry in body}
    assert names == {"검색1", "검색2"}


async def test_update_saved_search(client: AsyncClient, test_user: User) -> None:
    create_response = await client.post(
        "/api/v1/saved-searches",
        json={"user_id": test_user.id, "name": "원래 이름", "filters": {"category": "apartment"}},
    )
    saved_search_id = create_response.json()["id"]

    update_response = await client.put(
        f"/api/v1/saved-searches/{saved_search_id}",
        json={"name": "수정된 이름", "alert_enabled": False},
    )

    assert update_response.status_code == 200
    body = update_response.json()
    assert body["name"] == "수정된 이름"
    assert body["alert_enabled"] is False
    # filters를 전달하지 않았으므로 기존 값이 유지되어야 한다 (repository의 부분 업데이트 구현 기준).
    assert body["filters"] == {"category": "apartment"}


async def test_update_saved_search_not_found_returns_404(
    client: AsyncClient, test_user: User
) -> None:
    response = await client.put(
        "/api/v1/saved-searches/999999",
        json={"name": "존재하지 않음"},
    )

    assert response.status_code == 404


async def test_delete_saved_search(client: AsyncClient, test_user: User) -> None:
    create_response = await client.post(
        "/api/v1/saved-searches",
        json={"user_id": test_user.id, "name": "삭제 대상", "filters": {}},
    )
    saved_search_id = create_response.json()["id"]

    delete_response = await client.delete(
        f"/api/v1/saved-searches/{saved_search_id}", params={"user_id": test_user.id}
    )
    assert delete_response.status_code == 204

    listing = await client.get("/api/v1/saved-searches", params={"user_id": test_user.id})
    assert listing.json() == []


async def test_delete_saved_search_not_found_returns_404(
    client: AsyncClient, test_user: User
) -> None:
    response = await client.delete(
        "/api/v1/saved-searches/999999", params={"user_id": test_user.id}
    )

    assert response.status_code == 404
