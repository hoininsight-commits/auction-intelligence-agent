"""온비드(OnBid) 실제 Connector.

실제 API 연동은 후순위(지시서 §1). 구조만 열어두고, ONBID_API_KEY가 설정되지 않은
경우에는 명확한 에러를 던진다.
"""
from __future__ import annotations

from typing import Any

from app.core.config import settings
from app.ingestion.base import BaseConnector


class OnbidConnectorConfigError(RuntimeError):
    """ONBID_API_KEY 등 필수 설정값이 없을 때 발생한다."""


class OnbidConnector(BaseConnector):
    """온비드 공식 API 연동용 Connector (구조만 구현, 실제 호출 로직은 후순위)."""

    source = "onbid"

    def __init__(self) -> None:
        if not settings.ONBID_API_KEY:
            raise OnbidConnectorConfigError(
                "ONBID_API_KEY가 설정되지 않았습니다. 실제 온비드 API 연동을 사용하려면 "
                ".env에 ONBID_API_KEY를 설정하거나, ENABLE_MOCK_CONNECTORS=true로 "
                "MockOnbidConnector를 사용하세요."
            )
        self.api_key = settings.ONBID_API_KEY

    async def fetch_items(self, **kwargs) -> list[dict[str, Any]]:
        # 실제 온비드 Open API 연동은 후순위 기능이다 (지시서 §1).
        # 구조만 열어두고, 실제 HTTP 호출 로직은 아직 구현하지 않는다.
        raise NotImplementedError(
            "실제 온비드 API 연동은 아직 구현되지 않았습니다. "
            "MVP에서는 ENABLE_MOCK_CONNECTORS=true의 MockOnbidConnector를 사용하세요."
        )

    async def fetch_detail(self, source_item_id: str) -> dict[str, Any]:
        raise NotImplementedError(
            "실제 온비드 API 연동은 아직 구현되지 않았습니다."
        )
