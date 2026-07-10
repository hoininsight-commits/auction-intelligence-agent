"""참고 낙찰가 예측 라우터 (지시서 §7.4)."""
from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import get_db_session
from app.repositories.prediction_repository import PredictionRepository
from app.schemas.price_prediction import PredictPriceResponse
from app.services.price_prediction_service import PricePredictionService

router = APIRouter(tags=["predictions"])


@router.post(
    "/auction-items/{auction_item_id}/predict-price",
    response_model=PredictPriceResponse,
)
async def predict_price(
    auction_item_id: int,
    session: AsyncSession = Depends(get_db_session),
) -> PredictPriceResponse:
    repository = PredictionRepository(session)
    service = PricePredictionService(repository)

    calculation = await service.predict_and_save(auction_item_id)
    if calculation is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="경매 물건을 찾을 수 없습니다.")

    return PredictPriceResponse(
        auction_item_id=calculation.auction_item_id,
        predicted_price_low=calculation.predicted_price_low,
        predicted_price_mid=calculation.predicted_price_mid,
        predicted_price_high=calculation.predicted_price_high,
        predicted_rate_low=calculation.predicted_rate_low,
        predicted_rate_mid=calculation.predicted_rate_mid,
        predicted_rate_high=calculation.predicted_rate_high,
        confidence=calculation.confidence,
        model_version=calculation.model_version,
        explanation=calculation.explanation,
        disclaimer=calculation.disclaimer,
    )
