"""국토교통부 실거래가 실제 Connector.

실제 API 연동은 후순위(지시서 §1). 구조만 열어두고, MOLIT_API_KEY가 설정되지 않은
경우에는 명확한 에러를 던진다.
"""
from __future__ import annotations

from typing import Any

from app.core.config import settings
from app.ingestion.base import BaseConnector


class RealTransactionConnectorConfigError(RuntimeError):
    """MOLIT_API_KEY 등 필수 설정값이 없을 때 발생한다."""


class RealTransactionConnector(BaseConnector):
    """국토부 실거래가 공개 API 연동용 Connector (구조만 구현, 실제 호출 로직은 후순위)."""

    source = "molit"

    def __init__(self) -> None:
        if not settings.MOLIT_API_KEY:
            raise RealTransactionConnectorConfigError(
                "MOLIT_API_KEY가 설정되지 않았습니다. 실제 국토부 실거래가 API 연동을 사용하려면 "
                ".env에 MOLIT_API_KEY를 설정하거나, ENABLE_MOCK_CONNECTORS=true로 "
                "MockRealTransactionConnector를 사용하세요."
            )
        self.api_key = settings.MOLIT_API_KEY

    async def fetch_items(self, **kwargs) -> list[dict[str, Any]]:
        # 실제 국토부 실거래가 Open API 연동은 후순위 기능이다 (지시서 §1).
        raise NotImplementedError(
            "실제 국토부 실거래가 API 연동은 아직 구현되지 않았습니다. "
            "MVP에서는 ENABLE_MOCK_CONNECTORS=true의 MockRealTransactionConnector를 사용하세요."
        )

    async def fetch_detail(self, source_item_id: str) -> dict[str, Any]:
        raise NotImplementedError(
            "실제 국토부 실거래가 API 연동은 아직 구현되지 않았습니다."
        )
