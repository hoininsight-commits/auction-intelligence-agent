"""수익률 계산 라우터 (지시서 §7.7)."""

from __future__ import annotations

from fastapi import APIRouter

from app.schemas.profitability import (
    ProfitabilityCalculateRequest,
    ProfitabilityCalculateResponse,
)
from app.services import profitability_service

router = APIRouter(prefix="/profitability", tags=["profitability"])


@router.post("/calculate", response_model=ProfitabilityCalculateResponse)
async def calculate_profitability(
    payload: ProfitabilityCalculateRequest,
) -> ProfitabilityCalculateResponse:
    return profitability_service.calculate_profitability(payload)
