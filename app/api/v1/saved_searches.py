"""저장 검색 라우터 (지시서 §7.6)."""
from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import get_db_session
from app.schemas.saved_search import SavedSearchCreate, SavedSearchRead, SavedSearchUpdate
from app.services import saved_search_service
from app.services.saved_search_service import SavedSearchNotFoundError

router = APIRouter(prefix="/saved-searches", tags=["saved-searches"])


@router.post("", response_model=SavedSearchRead, status_code=status.HTTP_201_CREATED)
async def create_saved_search(
    payload: SavedSearchCreate,
    session: AsyncSession = Depends(get_db_session),
) -> SavedSearchRead:
    entry = await saved_search_service.create_saved_search(
        session, payload.user_id, payload.name, payload.filters, payload.alert_enabled
    )
    return SavedSearchRead.model_validate(entry)


@router.get("", response_model=list[SavedSearchRead])
async def list_saved_searches(
    user_id: int = Query(...),
    session: AsyncSession = Depends(get_db_session),
) -> list[SavedSearchRead]:
    entries = await saved_search_service.list_saved_searches(session, user_id)
    return [SavedSearchRead.model_validate(entry) for entry in entries]


@router.put("/{saved_search_id}", response_model=SavedSearchRead)
async def update_saved_search(
    saved_search_id: int,
    payload: SavedSearchUpdate,
    session: AsyncSession = Depends(get_db_session),
) -> SavedSearchRead:
    try:
        entry = await saved_search_service.update_saved_search(
            session,
            saved_search_id,
            payload.name,
            payload.filters,
            payload.alert_enabled,
        )
    except SavedSearchNotFoundError:
        raise HTTPException(status_code=404, detail="저장 검색을 찾을 수 없습니다.") from None
    return SavedSearchRead.model_validate(entry)


@router.delete("/{saved_search_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_saved_search(
    saved_search_id: int,
    user_id: int = Query(...),
    session: AsyncSession = Depends(get_db_session),
) -> None:
    deleted = await saved_search_service.delete_saved_search(session, saved_search_id, user_id)
    if not deleted:
        raise HTTPException(status_code=404, detail="저장 검색을 찾을 수 없습니다.")
