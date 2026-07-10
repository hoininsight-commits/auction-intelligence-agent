"""관리자 데이터 품질 라우터 (지시서 §7.8)."""

from __future__ import annotations

from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import get_db_session
from app.schemas.data_source import DataQualitySummaryResponse
from app.services.data_quality_service import DataQualityService

router = APIRouter(prefix="/admin", tags=["admin"])


@router.get("/data-quality/summary", response_model=DataQualitySummaryResponse)
async def get_data_quality_summary(
    session: AsyncSession = Depends(get_db_session),
) -> DataQualitySummaryResponse:
    service = DataQualityService(session)
    summary = await service.get_summary()

    return DataQualitySummaryResponse(
        total_items=summary.total_items,
        missing_appraisal_price=summary.missing_appraisal_price,
        missing_minimum_price=summary.missing_minimum_price,
        missing_coordinates=summary.missing_coordinates,
        past_bid_date_active_status=summary.past_bid_date_active_status,
        duplicate_case_numbers=summary.duplicate_case_numbers,
        prediction_missing=summary.prediction_missing,
        invalid_minimum_price_over_appraisal=summary.invalid_minimum_price_over_appraisal,
        missing_address=summary.missing_address,
    )
