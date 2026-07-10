"""notifications 테이블 모델 (지시서 §6.14)."""

from __future__ import annotations

from datetime import datetime

from sqlalchemy import BigInteger, ForeignKey, String, Text, func
from sqlalchemy.orm import Mapped, mapped_column

from app.models.base import Base


class Notification(Base):
    __tablename__ = "notifications"

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True)

    user_id: Mapped[int] = mapped_column(
        BigInteger, ForeignKey("users.id", ondelete="CASCADE"), nullable=False
    )
    auction_item_id: Mapped[int | None] = mapped_column(
        BigInteger, ForeignKey("auction_items.id", ondelete="SET NULL")
    )

    notification_type: Mapped[str | None] = mapped_column(String(50))
    title: Mapped[str | None] = mapped_column(String(200))
    message: Mapped[str | None] = mapped_column(Text)

    status: Mapped[str | None] = mapped_column(
        String(50), default="pending", server_default="pending"
    )
    scheduled_at: Mapped[datetime | None] = mapped_column()
    sent_at: Mapped[datetime | None] = mapped_column()

    created_at: Mapped[datetime] = mapped_column(server_default=func.now())
