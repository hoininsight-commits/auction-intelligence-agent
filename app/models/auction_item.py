"""auction_items 테이블 모델 (지시서 §6.3)."""
from __future__ import annotations

from datetime import datetime
from typing import TYPE_CHECKING

from sqlalchemy import BigInteger, Integer, Numeric, String, Text, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import Base

if TYPE_CHECKING:
    from app.models.price_prediction import PricePrediction
    from app.models.real_estate_detail import RealEstateDetail
    from app.models.risk_assessment import RiskAssessment
    from app.models.auction_result import AuctionResult
    from app.models.vehicle_detail import VehicleDetail


class AuctionItem(Base):
    __tablename__ = "auction_items"

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True)

    source: Mapped[str] = mapped_column(String(50), nullable=False)
    source_item_id: Mapped[str | None] = mapped_column(String(200))
    auction_type: Mapped[str] = mapped_column(String(50), nullable=False)

    case_number: Mapped[str | None] = mapped_column(String(100))
    item_number: Mapped[str | None] = mapped_column(String(50))
    category: Mapped[str | None] = mapped_column(String(50))
    sub_category: Mapped[str | None] = mapped_column(String(50))

    title: Mapped[str | None] = mapped_column(Text)
    address: Mapped[str | None] = mapped_column(Text)
    sido: Mapped[str | None] = mapped_column(String(50))
    sigungu: Mapped[str | None] = mapped_column(String(50))
    eupmyeondong: Mapped[str | None] = mapped_column(String(50))

    latitude: Mapped[float | None] = mapped_column(Numeric(10, 7))
    longitude: Mapped[float | None] = mapped_column(Numeric(10, 7))

    appraisal_price: Mapped[int | None] = mapped_column(BigInteger)
    minimum_price: Mapped[int | None] = mapped_column(BigInteger)
    deposit_price: Mapped[int | None] = mapped_column(BigInteger)

    bid_date: Mapped[datetime | None] = mapped_column()
    bid_location: Mapped[str | None] = mapped_column(Text)
    fail_count: Mapped[int] = mapped_column(Integer, default=0, server_default="0")

    status: Mapped[str | None] = mapped_column(String(50), default="active", server_default="active")

    view_count: Mapped[int] = mapped_column(Integer, default=0, server_default="0")
    watch_count: Mapped[int] = mapped_column(Integer, default=0, server_default="0")

    raw_source_record_id: Mapped[int | None] = mapped_column(BigInteger)

    created_at: Mapped[datetime] = mapped_column(server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(server_default=func.now(), onupdate=func.now())

    real_estate_detail: Mapped["RealEstateDetail | None"] = relationship(
        back_populates="auction_item", uselist=False, cascade="all, delete-orphan"
    )
    vehicle_detail: Mapped["VehicleDetail | None"] = relationship(
        back_populates="auction_item", uselist=False, cascade="all, delete-orphan"
    )
    results: Mapped[list["AuctionResult"]] = relationship(
        back_populates="auction_item", cascade="all, delete-orphan"
    )
    predictions: Mapped[list["PricePrediction"]] = relationship(
        back_populates="auction_item", cascade="all, delete-orphan"
    )
    risk_assessments: Mapped[list["RiskAssessment"]] = relationship(
        back_populates="auction_item", cascade="all, delete-orphan"
    )
