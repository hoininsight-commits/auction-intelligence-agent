"""공통 Pydantic v2 스키마 (페이지네이션 등).

Phase 2: 여러 스키마 모듈에서 공용으로 쓰는 최소한의 형태만 정의한다.
API 응답 스펙(필드명 등)은 지시서 §7을 참고해 Phase 3/4에서 확정한다.
"""
from typing import Generic, TypeVar

from pydantic import BaseModel, ConfigDict

T = TypeVar("T")


class ORMBase(BaseModel):
    """DB 모델 → 응답 스키마 변환을 위한 공통 설정."""

    model_config = ConfigDict(from_attributes=True)


class PaginationParams(BaseModel):
    page: int = 1
    page_size: int = 20


class PaginatedResponse(BaseModel, Generic[T]):
    items: list[T]
    total: int
    page: int
    page_size: int
