"""관심 물건 라우터 (지시서 §7.5)."""
from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import get_db_session
from app.schemas.watchlist import WatchlistCreate, WatchlistRead
from app.services import watchlist_service
from app.services.watchlist_service import WatchlistAlreadyExistsError

router = APIRouter(prefix="/watchlist", tags=["watchlist"])


@router.post("", response_model=WatchlistRead, status_code=status.HTTP_201_CREATED)
async def add_watchlist(
    payload: WatchlistCreate,
    session: AsyncSession = Depends(get_db_session),
) -> WatchlistRead:
    try:
        entry = await watchlist_service.add_to_watchlist(
            session, payload.user_id, payload.auction_item_id, payload.memo
        )
    except WatchlistAlreadyExistsError:
        raise HTTPException(status_code=409, detail="이미 관심 물건에 등록되어 있습니다.") from None
    return WatchlistRead.model_validate(entry)


@router.get("", response_model=list[WatchlistRead])
async def list_watchlist(
    user_id: int = Query(...),
    session: AsyncSession = Depends(get_db_session),
) -> list[WatchlistRead]:
    entries = await watchlist_service.list_watchlist(session, user_id)
    return [WatchlistRead.model_validate(entry) for entry in entries]


@router.delete("/{auction_item_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_watchlist(
    auction_item_id: int,
    user_id: int = Query(...),
    session: AsyncSession = Depends(get_db_session),
) -> None:
    deleted = await watchlist_service.remove_from_watchlist(session, user_id, auction_item_id)
    if not deleted:
        raise HTTPException(status_code=404, detail="관심 물건을 찾을 수 없습니다.")
