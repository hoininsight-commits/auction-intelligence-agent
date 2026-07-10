"""BaseConnector 인터페이스 (async fetch_items / fetch_detail, 지시서 §9.2).

모든 Connector(Mock/실제)는 이 추상 클래스를 상속한다.
"""

from __future__ import annotations

from abc import ABC, abstractmethod
from typing import Any


class BaseConnector(ABC):
    source: str

    @abstractmethod
    async def fetch_items(self, **kwargs) -> list[dict[str, Any]]:
        """수집 대상 원본 아이템 목록을 반환한다 (지시서 §9.3, §9.4 필드 형태)."""
        raise NotImplementedError

    @abstractmethod
    async def fetch_detail(self, source_item_id: str) -> dict[str, Any]:
        """단일 아이템의 상세 원본 데이터를 반환한다."""
        raise NotImplementedError
