"""vehicle_details 테이블 모델 (지시서 §6.5)."""
from __future__ import annotations

from datetime import datetime
from typing import TYPE_CHECKING

from sqlalchemy import BigInteger, ForeignKey, Integer, String, Text, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import Base

if TYPE_CHECKING:
    from app.models.auction_item import AuctionItem


class VehicleDetail(Base):
    __tablename__ = "vehicle_details"

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True)
    auction_item_id: Mapped[int | None] = mapped_column(
        BigInteger, ForeignKey("auction_items.id", ondelete="CASCADE")
    )

    manufacturer: Mapped[str | None] = mapped_column(String(100))
    model: Mapped[str | None] = mapped_column(String(100))
    trim: Mapped[str | None] = mapped_column(String(100))
    model_year: Mapped[int | None] = mapped_column(Integer)
    mileage: Mapped[int | None] = mapped_column(Integer)
    fuel_type: Mapped[str | None] = mapped_column(String(50))
    transmission: Mapped[str | None] = mapped_column(String(50))
    color: Mapped[str | None] = mapped_column(String(50))

    accident_history: Mapped[str | None] = mapped_column(Text)
    inspection_summary: Mapped[str | None] = mapped_column(Text)
    storage_location: Mapped[str | None] = mapped_column(Text)

    created_at: Mapped[datetime] = mapped_column(server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(server_default=func.now(), onupdate=func.now())

    auction_item: Mapped["AuctionItem"] = relationship(back_populates="vehicle_detail")
