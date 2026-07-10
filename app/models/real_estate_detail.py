"""real_estate_details 테이블 모델 (지시서 §6.4)."""
from __future__ import annotations

from datetime import date, datetime
from typing import TYPE_CHECKING

from sqlalchemy import BigInteger, Date, ForeignKey, Numeric, String, Text, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import Base

if TYPE_CHECKING:
    from app.models.auction_item import AuctionItem


class RealEstateDetail(Base):
    __tablename__ = "real_estate_details"

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True)
    auction_item_id: Mapped[int | None] = mapped_column(
        BigInteger, ForeignKey("auction_items.id", ondelete="CASCADE")
    )

    building_area: Mapped[float | None] = mapped_column(Numeric(12, 2))
    land_area: Mapped[float | None] = mapped_column(Numeric(12, 2))
    exclusive_area: Mapped[float | None] = mapped_column(Numeric(12, 2))

    floor_info: Mapped[str | None] = mapped_column(String(100))
    approval_date: Mapped[date | None] = mapped_column(Date)
    land_rights: Mapped[str | None] = mapped_column(Text)
    building_structure: Mapped[str | None] = mapped_column(Text)
    usage_type: Mapped[str | None] = mapped_column(String(100))

    appraisal_summary: Mapped[str | None] = mapped_column(Text)
    occupancy_summary: Mapped[str | None] = mapped_column(Text)
    tenant_summary: Mapped[str | None] = mapped_column(Text)
    registry_summary: Mapped[str | None] = mapped_column(Text)
    document_summary: Mapped[str | None] = mapped_column(Text)

    created_at: Mapped[datetime] = mapped_column(server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(server_default=func.now(), onupdate=func.now())

    auction_item: Mapped["AuctionItem"] = relationship(back_populates="real_estate_detail")
