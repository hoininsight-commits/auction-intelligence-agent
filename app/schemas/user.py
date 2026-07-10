"""사용자 Pydantic v2 스키마 (지시서 §6.2).

Phase 2: 최소한의 Read/Create 형태만 정의. 인증 관련 API 스키마는 이후 phase에서 필요 시 확장한다.
"""

from __future__ import annotations

from datetime import datetime

from pydantic import BaseModel

from app.schemas.common import ORMBase


class UserCreate(BaseModel):
    email: str
    nickname: str | None = None


class UserRead(ORMBase):
    id: int
    email: str
    nickname: str | None = None
    is_active: bool
    is_admin: bool
    created_at: datetime
    updated_at: datetime
