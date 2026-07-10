"""price_predictions 테이블 모델 (지시서 §6.7)."""
from __future__ import annotations

from datetime import datetime
from typing import Any

from sqlalchemy import BigInteger, ForeignKey, Numeric, String, Text, func
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import Base


class PricePrediction(Base):
    __tablename__ = "price_predictions"

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True)
    auction_item_id: Mapped[int | None] = mapped_column(
        BigInteger, ForeignKey("auction_items.id", ondelete="CASCADE")
    )

    predicted_price_low: Mapped[int | None] = mapped_column(BigInteger)
    predicted_price_mid: Mapped[int | None] = mapped_column(BigInteger)
    predicted_price_high: Mapped[int | None] = mapped_column(BigInteger)

    predicted_rate_low: Mapped[float | None] = mapped_column(Numeric(6, 2))
    predicted_rate_mid: Mapped[float | None] = mapped_column(Numeric(6, 2))
    predicted_rate_high: Mapped[float | None] = mapped_column(Numeric(6, 2))

    confidence: Mapped[str | None] = mapped_column(String(50))
    model_version: Mapped[str | None] = mapped_column(String(50))
    explanation: Mapped[dict[str, Any] | None] = mapped_column(JSONB)

    disclaimer: Mapped[str | None] = mapped_column(Text)

    created_at: Mapped[datetime] = mapped_column(server_default=func.now())

    auction_item: Mapped["AuctionItem"] = relationship(back_populates="predictions")
