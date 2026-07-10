"""risk_assessments 테이블 모델 (지시서 §6.12)."""

from __future__ import annotations

from datetime import datetime
from typing import TYPE_CHECKING, Any

from sqlalchemy import BigInteger, ForeignKey, Numeric, String, Text, func
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import Base

if TYPE_CHECKING:
    from app.models.auction_item import AuctionItem


class RiskAssessment(Base):
    __tablename__ = "risk_assessments"

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True)
    auction_item_id: Mapped[int | None] = mapped_column(
        BigInteger, ForeignKey("auction_items.id", ondelete="CASCADE")
    )

    risk_level: Mapped[str | None] = mapped_column(String(50))
    legal_risk_score: Mapped[float | None] = mapped_column(Numeric(5, 2))
    occupancy_risk_score: Mapped[float | None] = mapped_column(Numeric(5, 2))
    asset_risk_score: Mapped[float | None] = mapped_column(Numeric(5, 2))

    risk_factors: Mapped[dict[str, Any] | None] = mapped_column(JSONB)
    disclaimer: Mapped[str | None] = mapped_column(Text)

    created_at: Mapped[datetime] = mapped_column(server_default=func.now())

    auction_item: Mapped["AuctionItem"] = relationship(back_populates="risk_assessments")
