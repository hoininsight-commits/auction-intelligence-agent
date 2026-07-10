"""저장 검색 Pydantic v2 스키마 (지시서 §7.6)."""

from __future__ import annotations

from datetime import datetime
from typing import Any

from pydantic import BaseModel

from app.schemas.common import ORMBase


class SavedSearchCreate(BaseModel):
    user_id: int
    name: str | None = None
    filters: dict[str, Any] | None = None
    alert_enabled: bool = True


class SavedSearchUpdate(BaseModel):
    name: str | None = None
    filters: dict[str, Any] | None = None
    alert_enabled: bool | None = None


class SavedSearchRead(ORMBase):
    id: int
    user_id: int
    name: str | None = None
    filters: dict[str, Any] | None = None
    alert_enabled: bool
    created_at: datetime
    updated_at: datetime
