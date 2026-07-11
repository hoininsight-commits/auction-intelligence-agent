"""경매 물건 상세 비즈니스 로직 (지시서 §7.3)."""

from __future__ import annotations

from sqlalchemy.ext.asyncio import AsyncSession

from app.core.disclaimers import INVESTMENT_DISCLAIMER
from app.models import AuctionItem
from app.repositories import auction_item_repository
from app.schemas.auction_item import (
    AuctionItemDetailResponse,
    LatestPredictionRead,
    NearbyTransaction,
    RealEstateDetailRead,
    RiskAssessmentSummary,
    VehicleDetailRead,
)


def _extract_risk_factors(risk_factors: dict | None) -> list[str]:
    if not risk_factors:
        return []
    if isinstance(risk_factors, dict):
        factors = risk_factors.get("factors", [])
        return list(factors) if isinstance(factors, list) else []
    if isinstance(risk_factors, list):
        return risk_factors
    return []


async def get_auction_item_detail(
    session: AsyncSession, auction_item_id: int
) -> AuctionItemDetailResponse | None:
    item: AuctionItem | None = await auction_item_repository.get_auction_item_by_id(
        session, auction_item_id
    )
    if item is None:
        return None

    prediction = await auction_item_repository.get_latest_prediction(session, auction_item_id)
    risk_assessment = await auction_item_repository.get_latest_risk_assessment(
        session, auction_item_id
    )
    nearby_transactions = await auction_item_repository.get_nearby_transactions(
        session, item.sido, item.sigungu
    )

    view_count = await auction_item_repository.increment_view_count(session, auction_item_id)
    await session.commit()

    latest_prediction = (
        LatestPredictionRead(
            predicted_price_low=prediction.predicted_price_low,
            predicted_price_mid=prediction.predicted_price_mid,
            predicted_price_high=prediction.predicted_price_high,
            predicted_rate_low=float(prediction.predicted_rate_low)
            if prediction.predicted_rate_low is not None
            else None,
            predicted_rate_mid=float(prediction.predicted_rate_mid)
            if prediction.predicted_rate_mid is not None
            else None,
            predicted_rate_high=float(prediction.predicted_rate_high)
            if prediction.predicted_rate_high is not None
            else None,
            confidence=prediction.confidence,
            model_version=prediction.model_version,
            verdict=(prediction.explanation or {}).get("verdict"),
        )
        if prediction
        else None
    )

    risk_summary = (
        RiskAssessmentSummary(
            risk_level=risk_assessment.risk_level,
            risk_factors=_extract_risk_factors(risk_assessment.risk_factors),
        )
        if risk_assessment
        else None
    )

    return AuctionItemDetailResponse(
        id=item.id,
        source=item.source,
        auction_type=item.auction_type,
        case_number=item.case_number,
        item_number=item.item_number,
        category=item.category,
        title=item.title,
        address=item.address,
        appraisal_price=item.appraisal_price,
        minimum_price=item.minimum_price,
        deposit_price=item.deposit_price,
        fail_count=item.fail_count,
        bid_date=item.bid_date,
        view_count=view_count if view_count is not None else item.view_count,
        watch_count=item.watch_count,
        real_estate_detail=RealEstateDetailRead.model_validate(item.real_estate_detail)
        if item.real_estate_detail
        else None,
        vehicle_detail=VehicleDetailRead.model_validate(item.vehicle_detail)
        if item.vehicle_detail
        else None,
        latest_prediction=latest_prediction,
        risk_assessment=risk_summary,
        nearby_transactions=[
            NearbyTransaction(
                complex_name=tx.complex_name,
                address=tx.address,
                exclusive_area=float(tx.exclusive_area) if tx.exclusive_area is not None else None,
                deal_price=tx.deal_price,
                deal_year=tx.deal_year,
                deal_month=tx.deal_month,
                deal_day=tx.deal_day,
                floor_info=tx.floor_info,
                build_year=tx.build_year,
            )
            for tx in nearby_transactions
        ],
        disclaimer=INVESTMENT_DISCLAIMER,
    )
