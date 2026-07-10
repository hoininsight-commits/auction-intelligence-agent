"""저장 검색 서비스 (지시서 §7.6)."""

from __future__ import annotations

from typing import Any

from sqlalchemy.ext.asyncio import AsyncSession

from app.models import SavedSearch
from app.repositories import saved_search_repository


class SavedSearchNotFoundError(Exception):
    """저장 검색을 찾을 수 없거나 사용자가 소유하지 않은 경우."""


async def create_saved_search(
    session: AsyncSession,
    user_id: int,
    name: str | None,
    filters: dict[str, Any] | None,
    alert_enabled: bool,
) -> SavedSearch:
    entry = await saved_search_repository.create_saved_search(
        session, user_id, name, filters, alert_enabled
    )
    await session.commit()
    return entry


async def list_saved_searches(session: AsyncSession, user_id: int) -> list[SavedSearch]:
    return await saved_search_repository.list_saved_searches_by_user(session, user_id)


async def update_saved_search(
    session: AsyncSession,
    saved_search_id: int,
    name: str | None,
    filters: dict[str, Any] | None,
    alert_enabled: bool | None,
) -> SavedSearch:
    entry = await saved_search_repository.get_saved_search_by_id(session, saved_search_id)
    if entry is None:
        raise SavedSearchNotFoundError()

    updated = await saved_search_repository.update_saved_search(
        session, entry, name, filters, alert_enabled
    )
    await session.commit()
    return updated


async def delete_saved_search(session: AsyncSession, saved_search_id: int, user_id: int) -> bool:
    deleted = await saved_search_repository.delete_saved_search(session, saved_search_id, user_id)
    await session.commit()
    return deleted
