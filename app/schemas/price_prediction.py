"""참고 낙찰가 예측 Pydantic v2 스키마 (지시서 §7.4, §8)."""

from __future__ import annotations

from datetime import datetime
from typing import Any

from pydantic import BaseModel

from app.schemas.common import ORMBase


class PricePredictionRead(ORMBase):
    id: int
    auction_item_id: int | None = None

    predicted_price_low: int | None = None
    predicted_price_mid: int | None = None
    predicted_price_high: int | None = None

    predicted_rate_low: float | None = None
    predicted_rate_mid: float | None = None
    predicted_rate_high: float | None = None

    confidence: str | None = None
    model_version: str | None = None
    explanation: dict[str, Any] | None = None

    disclaimer: str | None = None
    created_at: datetime


class PredictPriceResponse(BaseModel):
    """POST /api/v1/auction-items/{id}/predict-price 응답 (지시서 §7.4 응답 예시 그대로)."""

    auction_item_id: int

    predicted_price_low: int
    predicted_price_mid: int
    predicted_price_high: int

    predicted_rate_low: float | None = None
    predicted_rate_mid: float | None = None
    predicted_rate_high: float | None = None

    confidence: str
    model_version: str
    explanation: list[str]

    disclaimer: str
