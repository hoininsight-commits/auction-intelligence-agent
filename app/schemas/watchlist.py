"""관심 물건 Pydantic v2 스키마 (지시서 §7.5)."""

from __future__ import annotations

from datetime import datetime

from pydantic import BaseModel

from app.schemas.common import ORMBase


class WatchlistCreate(BaseModel):
    user_id: int
    auction_item_id: int
    memo: str | None = None


class WatchlistRead(ORMBase):
    id: int
    user_id: int
    auction_item_id: int | None = None
    memo: str | None = None
    created_at: datetime
