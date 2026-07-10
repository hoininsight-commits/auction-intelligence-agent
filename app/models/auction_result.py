"""auction_results 테이블 모델 (지시서 §6.6)."""
from __future__ import annotations

from datetime import date, datetime
from typing import TYPE_CHECKING

from sqlalchemy import BigInteger, Date, ForeignKey, Integer, Numeric, String, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import Base

if TYPE_CHECKING:
    from app.models.auction_item import AuctionItem


class AuctionResult(Base):
    __tablename__ = "auction_results"

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True)
    auction_item_id: Mapped[int | None] = mapped_column(
        BigInteger, ForeignKey("auction_items.id", ondelete="CASCADE")
    )

    result_status: Mapped[str | None] = mapped_column(String(50))
    winning_price: Mapped[int | None] = mapped_column(BigInteger)
    winning_rate: Mapped[float | None] = mapped_column(Numeric(6, 2))
    bidder_count: Mapped[int | None] = mapped_column(Integer)
    result_date: Mapped[date | None] = mapped_column(Date)

    created_at: Mapped[datetime] = mapped_column(server_default=func.now())

    auction_item: Mapped["AuctionItem"] = relationship(back_populates="results")
