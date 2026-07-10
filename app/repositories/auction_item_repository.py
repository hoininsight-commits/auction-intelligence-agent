"""auction_items DB 접근 계층 (지시서 §7.2, §7.3).

검색/상세 API에서 필요한 쿼리를 담당한다. 최근 예상 낙찰가(price_predictions)와
최근 위험도(risk_assessments)는 Phase 4 서비스 완성을 기다리지 않고 이 레포지토리에서
직접 SELECT 해서 채운다.
"""
from __future__ import annotations

from datetime import datetime
from typing import Any

from sqlalchemy import Select, and_, func, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.core.constants import RISK_LEVEL_ORDER
from app.models import (
    AuctionItem,
    PricePrediction,
    PropertyTransaction,
    RealEstateDetail,
    RiskAssessment,
    VehicleDetail,
)

SORT_OPTIONS: dict[str, tuple[Any, str]] = {
    "bid_date_asc": (AuctionItem.bid_date, "asc"),
    "bid_date_desc": (AuctionItem.bid_date, "desc"),
    "minimum_price_asc": (AuctionItem.minimum_price, "asc"),
    "minimum_price_desc": (AuctionItem.minimum_price, "desc"),
    "appraisal_price_asc": (AuctionItem.appraisal_price, "asc"),
    "appraisal_price_desc": (AuctionItem.appraisal_price, "desc"),
    "fail_count_desc": (AuctionItem.fail_count, "desc"),
    "created_at_desc": (AuctionItem.created_at, "desc"),
}


def _latest_prediction_subquery():
    return (
        select(
            PricePrediction.auction_item_id.label("auction_item_id"),
            func.max(PricePrediction.created_at).label("max_created_at"),
        )
        .group_by(PricePrediction.auction_item_id)
        .subquery()
    )


def _latest_risk_subquery():
    return (
        select(
            RiskAssessment.auction_item_id.label("auction_item_id"),
            func.max(RiskAssessment.created_at).label("max_created_at"),
        )
        .group_by(RiskAssessment.auction_item_id)
        .subquery()
    )


def _build_filtered_query(filters: dict[str, Any]) -> tuple[Select, Any, Any]:
    """검색 필터가 적용된 (AuctionItem, PricePrediction, RiskAssessment) 기본 join 쿼리를 만든다."""
    latest_pred = _latest_prediction_subquery()
    latest_risk = _latest_risk_subquery()

    stmt = (
        select(AuctionItem, PricePrediction, RiskAssessment)
        .outerjoin(latest_pred, latest_pred.c.auction_item_id == AuctionItem.id)
        .outerjoin(
            PricePrediction,
            and_(
                PricePrediction.auction_item_id == latest_pred.c.auction_item_id,
                PricePrediction.created_at == latest_pred.c.max_created_at,
            ),
        )
        .outerjoin(latest_risk, latest_risk.c.auction_item_id == AuctionItem.id)
        .outerjoin(
            RiskAssessment,
            and_(
                RiskAssessment.auction_item_id == latest_risk.c.auction_item_id,
                RiskAssessment.created_at == latest_risk.c.max_created_at,
            ),
        )
    )

    if filters.get("source"):
        stmt = stmt.where(AuctionItem.source == filters["source"])
    if filters.get("auction_type"):
        stmt = stmt.where(AuctionItem.auction_type == filters["auction_type"])
    if filters.get("category"):
        stmt = stmt.where(AuctionItem.category == filters["category"])
    if filters.get("sido"):
        stmt = stmt.where(AuctionItem.sido == filters["sido"])
    if filters.get("sigungu"):
        stmt = stmt.where(AuctionItem.sigungu == filters["sigungu"])
    if filters.get("eupmyeondong"):
        stmt = stmt.where(AuctionItem.eupmyeondong == filters["eupmyeondong"])
    if filters.get("min_price") is not None:
        stmt = stmt.where(AuctionItem.minimum_price >= filters["min_price"])
    if filters.get("max_price") is not None:
        stmt = stmt.where(AuctionItem.minimum_price <= filters["max_price"])
    if filters.get("min_appraisal_price") is not None:
        stmt = stmt.where(AuctionItem.appraisal_price >= filters["min_appraisal_price"])
    if filters.get("max_appraisal_price") is not None:
        stmt = stmt.where(AuctionItem.appraisal_price <= filters["max_appraisal_price"])
    if filters.get("bid_date_from") is not None:
        stmt = stmt.where(AuctionItem.bid_date >= filters["bid_date_from"])
    if filters.get("bid_date_to") is not None:
        stmt = stmt.where(AuctionItem.bid_date <= filters["bid_date_to"])
    if filters.get("fail_count") is not None:
        stmt = stmt.where(AuctionItem.fail_count == filters["fail_count"])
    if filters.get("status"):
        stmt = stmt.where(AuctionItem.status == filters["status"])
    if filters.get("min_predicted_rate") is not None:
        stmt = stmt.where(PricePrediction.predicted_rate_mid >= filters["min_predicted_rate"])
    if filters.get("max_risk_level"):
        max_order = RISK_LEVEL_ORDER.get(filters["max_risk_level"])
        if max_order is not None:
            allowed_levels = [level for level, order in RISK_LEVEL_ORDER.items() if order <= max_order]
            stmt = stmt.where(RiskAssessment.risk_level.in_(allowed_levels))

    return stmt, latest_pred, latest_risk


async def search_auction_items(
    session: AsyncSession,
    filters: dict[str, Any],
    sort: str,
    page: int,
    limit: int,
) -> tuple[list[tuple[AuctionItem, PricePrediction | None, RiskAssessment | None]], int]:
    stmt, _, _ = _build_filtered_query(filters)

    count_stmt = select(func.count()).select_from(
        stmt.with_only_columns(AuctionItem.id).distinct().subquery()
    )
    total = (await session.execute(count_stmt)).scalar_one()

    sort_column, direction = SORT_OPTIONS.get(sort, SORT_OPTIONS["bid_date_asc"])
    order_by = sort_column.desc() if direction == "desc" else sort_column.asc()
    stmt = stmt.order_by(order_by, AuctionItem.id.asc()).offset((page - 1) * limit).limit(limit)

    result = await session.execute(stmt)
    rows = result.all()
    return [(row[0], row[1], row[2]) for row in rows], total


async def get_auction_item_by_id(session: AsyncSession, auction_item_id: int) -> AuctionItem | None:
    stmt = (
        select(AuctionItem)
        .where(AuctionItem.id == auction_item_id)
        .options(
            selectinload(AuctionItem.real_estate_detail),
            selectinload(AuctionItem.vehicle_detail),
        )
    )
    return (await session.execute(stmt)).scalar_one_or_none()


async def get_latest_prediction(session: AsyncSession, auction_item_id: int) -> PricePrediction | None:
    stmt = (
        select(PricePrediction)
        .where(PricePrediction.auction_item_id == auction_item_id)
        .order_by(PricePrediction.created_at.desc())
        .limit(1)
    )
    return (await session.execute(stmt)).scalar_one_or_none()


async def get_latest_risk_assessment(session: AsyncSession, auction_item_id: int) -> RiskAssessment | None:
    stmt = (
        select(RiskAssessment)
        .where(RiskAssessment.auction_item_id == auction_item_id)
        .order_by(RiskAssessment.created_at.desc())
        .limit(1)
    )
    return (await session.execute(stmt)).scalar_one_or_none()


async def get_nearby_transactions(
    session: AsyncSession,
    sido: str | None,
    sigungu: str | None,
    limit: int = 5,
) -> list[PropertyTransaction]:
    if not sido and not sigungu:
        return []

    stmt = select(PropertyTransaction)
    if sido:
        stmt = stmt.where(PropertyTransaction.sido == sido)
    if sigungu:
        stmt = stmt.where(PropertyTransaction.sigungu == sigungu)
    stmt = stmt.order_by(PropertyTransaction.created_at.desc()).limit(limit)

    result = await session.execute(stmt)
    return list(result.scalars().all())
