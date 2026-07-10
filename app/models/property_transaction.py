"""property_transactions 테이블 모델 (지시서 §6.11)."""

from __future__ import annotations

from datetime import datetime

from sqlalchemy import BigInteger, Integer, Numeric, String, Text, func
from sqlalchemy.orm import Mapped, mapped_column

from app.models.base import Base


class PropertyTransaction(Base):
    __tablename__ = "property_transactions"

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True)

    property_type: Mapped[str | None] = mapped_column(String(50))
    address: Mapped[str | None] = mapped_column(Text)

    sido: Mapped[str | None] = mapped_column(String(50))
    sigungu: Mapped[str | None] = mapped_column(String(50))
    eupmyeondong: Mapped[str | None] = mapped_column(String(50))

    complex_name: Mapped[str | None] = mapped_column(String(200))
    exclusive_area: Mapped[float | None] = mapped_column(Numeric(12, 2))

    deal_price: Mapped[int | None] = mapped_column(BigInteger)

    deal_year: Mapped[int | None] = mapped_column(Integer)
    deal_month: Mapped[int | None] = mapped_column(Integer)
    deal_day: Mapped[int | None] = mapped_column(Integer)

    floor_info: Mapped[str | None] = mapped_column(String(50))
    build_year: Mapped[int | None] = mapped_column(Integer)

    source: Mapped[str | None] = mapped_column(String(50))

    created_at: Mapped[datetime] = mapped_column(server_default=func.now())
