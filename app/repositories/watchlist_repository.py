"""user_watchlist DB 접근 계층 (지시서 §7.5)."""

from __future__ import annotations

from sqlalchemy import delete, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models import UserWatchlist


async def create_watchlist_entry(
    session: AsyncSession, user_id: int, auction_item_id: int, memo: str | None
) -> UserWatchlist:
    entry = UserWatchlist(user_id=user_id, auction_item_id=auction_item_id, memo=memo)
    session.add(entry)
    await session.flush()
    await session.refresh(entry)
    return entry


async def get_watchlist_entry(
    session: AsyncSession, user_id: int, auction_item_id: int
) -> UserWatchlist | None:
    stmt = select(UserWatchlist).where(
        UserWatchlist.user_id == user_id,
        UserWatchlist.auction_item_id == auction_item_id,
    )
    return (await session.execute(stmt)).scalar_one_or_none()


async def list_watchlist_by_user(session: AsyncSession, user_id: int) -> list[UserWatchlist]:
    stmt = (
        select(UserWatchlist)
        .where(UserWatchlist.user_id == user_id)
        .order_by(UserWatchlist.created_at.desc())
    )
    result = await session.execute(stmt)
    return list(result.scalars().all())


async def delete_watchlist_entry(session: AsyncSession, user_id: int, auction_item_id: int) -> bool:
    stmt = delete(UserWatchlist).where(
        UserWatchlist.user_id == user_id,
        UserWatchlist.auction_item_id == auction_item_id,
    )
    result = await session.execute(stmt)
    return result.rowcount > 0
