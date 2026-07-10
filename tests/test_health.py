"""Health 테스트 (지시서 §13.1)."""
from __future__ import annotations

from httpx import AsyncClient


async def test_health_check_returns_200(client: AsyncClient) -> None:
    response = await client.get("/api/v1/health")

    assert response.status_code == 200
    body = response.json()
    assert body["status"] == "ok"
    assert body["service"]
