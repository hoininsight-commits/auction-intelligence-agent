"""경매 물건 검색 비즈니스 로직 (지시서 §7.2)."""
from __future__ import annotations

import math
from datetime import datetime
from typing import Any

from sqlalchemy.ext.asyncio import AsyncSession

from app.repositories import auction_item_repository
from app.repositories.auction_item_repository import SORT_OPTIONS
from app.schemas.auction_item import (
    AuctionItemSearchItem,
    AuctionItemSearchPagination,
    AuctionItemSearchResponse,
)

DEFAULT_SORT = "bid_date_asc"
DEFAULT_PAGE = 1
DEFAULT_LIMIT = 20


def _parse_datetime(value: str | None) -> datetime | None:
    if not value:
        return None
    try:
        return datetime.fromisoformat(value)
    except ValueError:
        return datetime.strptime(value, "%Y-%m-%d")


async def search_auction_items(
    session: AsyncSession,
    *,
    source: str | None = None,
    auction_type: str | None = None,
    category: str | None = None,
    sido: str | None = None,
    sigungu: str | None = None,
    eupmyeondong: str | None = None,
    min_price: int | None = None,
    max_price: int | None = None,
    min_appraisal_price: int | None = None,
    max_appraisal_price: int | None = None,
    bid_date_from: str | None = None,
    bid_date_to: str | None = None,
    fail_count: int | None = None,
    status: str | None = None,
    min_predicted_rate: float | None = None,
    max_risk_level: str | None = None,
    sort: str = DEFAULT_SORT,
    page: int = DEFAULT_PAGE,
    limit: int = DEFAULT_LIMIT,
) -> AuctionItemSearchResponse:
    if sort not in SORT_OPTIONS:
        sort = DEFAULT_SORT
    page = max(page, 1)
    limit = max(limit, 1)

    filters: dict[str, Any] = {
        "source": source,
        "auction_type": auction_type,
        "category": category,
        "sido": sido,
        "sigungu": sigungu,
        "eupmyeondong": eupmyeondong,
        "min_price": min_price,
        "max_price": max_price,
        "min_appraisal_price": min_appraisal_price,
        "max_appraisal_price": max_appraisal_price,
        "bid_date_from": _parse_datetime(bid_date_from),
        "bid_date_to": _parse_datetime(bid_date_to),
        "fail_count": fail_count,
        "status": status,
        "min_predicted_rate": min_predicted_rate,
        "max_risk_level": max_risk_level,
    }

    rows, total = await auction_item_repository.search_auction_items(session, filters, sort, page, limit)

    items = [
        AuctionItemSearchItem(
            id=item.id,
            source=item.source,
            auction_type=item.auction_type,
            case_number=item.case_number,
            item_number=item.item_number,
            category=item.category,
            title=item.title,
            address=item.address,
            sido=item.sido,
            sigungu=item.sigungu,
            appraisal_price=item.appraisal_price,
            minimum_price=item.minimum_price,
            fail_count=item.fail_count,
            bid_date=item.bid_date,
            predicted_price_mid=prediction.predicted_price_mid if prediction else None,
            predicted_rate_mid=float(prediction.predicted_rate_mid)
            if prediction and prediction.predicted_rate_mid is not None
            else None,
            risk_level=risk.risk_level if risk else None,
            status=item.status,
        )
        for item, prediction, risk in rows
    ]

    total_pages = math.ceil(total / limit) if total else 0

    return AuctionItemSearchResponse(
        items=items,
        pagination=AuctionItemSearchPagination(
            page=page,
            limit=limit,
            total=total,
            total_pages=total_pages,
        ),
    )
