"""saved_searches DB 접근 계층 (지시서 §7.6)."""
from __future__ import annotations

from typing import Any

from sqlalchemy import delete, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models import SavedSearch


async def create_saved_search(
    session: AsyncSession,
    user_id: int,
    name: str | None,
    filters: dict[str, Any] | None,
    alert_enabled: bool,
) -> SavedSearch:
    entry = SavedSearch(user_id=user_id, name=name, filters=filters, alert_enabled=alert_enabled)
    session.add(entry)
    await session.flush()
    await session.refresh(entry)
    return entry


async def list_saved_searches_by_user(session: AsyncSession, user_id: int) -> list[SavedSearch]:
    stmt = (
        select(SavedSearch)
        .where(SavedSearch.user_id == user_id)
        .order_by(SavedSearch.created_at.desc())
    )
    result = await session.execute(stmt)
    return list(result.scalars().all())


async def get_saved_search_by_id(session: AsyncSession, saved_search_id: int) -> SavedSearch | None:
    stmt = select(SavedSearch).where(SavedSearch.id == saved_search_id)
    return (await session.execute(stmt)).scalar_one_or_none()


async def update_saved_search(
    session: AsyncSession,
    saved_search: SavedSearch,
    name: str | None,
    filters: dict[str, Any] | None,
    alert_enabled: bool | None,
) -> SavedSearch:
    if name is not None:
        saved_search.name = name
    if filters is not None:
        saved_search.filters = filters
    if alert_enabled is not None:
        saved_search.alert_enabled = alert_enabled
    await session.flush()
    await session.refresh(saved_search)
    return saved_search


async def delete_saved_search(session: AsyncSession, saved_search_id: int, user_id: int) -> bool:
    stmt = delete(SavedSearch).where(
        SavedSearch.id == saved_search_id,
        SavedSearch.user_id == user_id,
    )
    result = await session.execute(stmt)
    return result.rowcount > 0
