"""관심 물건 서비스 (지시서 §7.5)."""

from __future__ import annotations

from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession

from app.models import UserWatchlist
from app.repositories import watchlist_repository


class WatchlistAlreadyExistsError(Exception):
    """동일한 (user_id, auction_item_id) 조합이 이미 관심 물건에 등록된 경우."""


async def add_to_watchlist(
    session: AsyncSession, user_id: int, auction_item_id: int, memo: str | None
) -> UserWatchlist:
    existing = await watchlist_repository.get_watchlist_entry(session, user_id, auction_item_id)
    if existing is not None:
        raise WatchlistAlreadyExistsError()

    try:
        entry = await watchlist_repository.create_watchlist_entry(
            session, user_id, auction_item_id, memo
        )
        await session.commit()
        return entry
    except IntegrityError:
        await session.rollback()
        raise WatchlistAlreadyExistsError() from None


async def list_watchlist(session: AsyncSession, user_id: int) -> list[UserWatchlist]:
    return await watchlist_repository.list_watchlist_by_user(session, user_id)


async def remove_from_watchlist(session: AsyncSession, user_id: int, auction_item_id: int) -> bool:
    deleted = await watchlist_repository.delete_watchlist_entry(session, user_id, auction_item_id)
    await session.commit()
    return deleted
