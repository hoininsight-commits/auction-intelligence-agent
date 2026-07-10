"""raw_source_records 테이블 모델 (지시서 §6.10)."""
from __future__ import annotations

from datetime import datetime
from typing import Any

from sqlalchemy import BigInteger, String, func
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import Mapped, mapped_column

from app.models.base import Base


class RawSourceRecord(Base):
    __tablename__ = "raw_source_records"

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True)

    source: Mapped[str] = mapped_column(String(50), nullable=False)
    source_record_id: Mapped[str | None] = mapped_column(String(200))
    record_type: Mapped[str | None] = mapped_column(String(50))

    raw_payload: Mapped[dict[str, Any]] = mapped_column(JSONB, nullable=False)
    fetched_at: Mapped[datetime] = mapped_column(server_default=func.now())

    checksum: Mapped[str | None] = mapped_column(String(128))

    created_at: Mapped[datetime] = mapped_column(server_default=func.now())
