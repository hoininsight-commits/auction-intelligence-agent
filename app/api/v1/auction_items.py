"""경매 물건 검색/상세 라우터 (지시서 §7.2, §7.3)."""

from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import get_db_session
from app.services import auction_detail_service, auction_search_service
from app.schemas.auction_item import AuctionItemDetailResponse, AuctionItemSearchResponse

router = APIRouter(prefix="/auction-items", tags=["auction-items"])


@router.get("", response_model=AuctionItemSearchResponse)
async def search_auction_items(
    source: str | None = Query(default=None),
    auction_type: str | None = Query(default=None),
    category: str | None = Query(default=None),
    sido: str | None = Query(default=None),
    sigungu: str | None = Query(default=None),
    eupmyeondong: str | None = Query(default=None),
    min_price: int | None = Query(default=None),
    max_price: int | None = Query(default=None),
    min_appraisal_price: int | None = Query(default=None),
    max_appraisal_price: int | None = Query(default=None),
    bid_date_from: str | None = Query(default=None),
    bid_date_to: str | None = Query(default=None),
    fail_count: int | None = Query(default=None),
    status: str | None = Query(default=None),
    min_predicted_rate: float | None = Query(default=None),
    max_risk_level: str | None = Query(default=None),
    sort: str = Query(default="bid_date_asc"),
    page: int = Query(default=1, ge=1),
    limit: int = Query(default=20, ge=1, le=100),
    session: AsyncSession = Depends(get_db_session),
) -> AuctionItemSearchResponse:
    return await auction_search_service.search_auction_items(
        session,
        source=source,
        auction_type=auction_type,
        category=category,
        sido=sido,
        sigungu=sigungu,
        eupmyeondong=eupmyeondong,
        min_price=min_price,
        max_price=max_price,
        min_appraisal_price=min_appraisal_price,
        max_appraisal_price=max_appraisal_price,
        bid_date_from=bid_date_from,
        bid_date_to=bid_date_to,
        fail_count=fail_count,
        status=status,
        min_predicted_rate=min_predicted_rate,
        max_risk_level=max_risk_level,
        sort=sort,
        page=page,
        limit=limit,
    )


@router.get("/{auction_item_id}", response_model=AuctionItemDetailResponse)
async def get_auction_item_detail(
    auction_item_id: int,
    session: AsyncSession = Depends(get_db_session),
) -> AuctionItemDetailResponse:
    detail = await auction_detail_service.get_auction_item_detail(session, auction_item_id)
    if detail is None:
        raise HTTPException(status_code=404, detail="경매 물건을 찾을 수 없습니다.")
    return detail
