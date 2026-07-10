"""주소 -> 좌표 지오코딩 서비스.

MVP 스텁: 실제 지오코딩 API(카카오/네이버) 호출은 구현하지 않는다.
KAKAO_MAP_API_KEY/NAVER_MAP_API_KEY가 없으면 좌표 None을 반환한다.
좌표(latitude/longitude) 필드는 항상 확보해 두어 추후 PostGIS 연결을 전제로 한다
(CLAUDE.md 데이터 흐름 원칙 5).
"""

from __future__ import annotations

from dataclasses import dataclass

from app.core.config import settings


@dataclass(frozen=True)
class GeocodeResult:
    latitude: float | None
    longitude: float | None


class GeocodingService:
    """주소 문자열을 좌표로 변환하는 서비스.

    실제 지오코딩 API 연동은 후순위(지시서 §1). API 키가 없으면 좌표 None을 반환하는
    스텁 수준으로만 구현한다.
    """

    def __init__(self) -> None:
        self.kakao_api_key = settings.KAKAO_MAP_API_KEY
        self.naver_api_key = settings.NAVER_MAP_API_KEY

    @property
    def is_enabled(self) -> bool:
        return bool(self.kakao_api_key or self.naver_api_key)

    async def geocode(self, address: str | None) -> GeocodeResult:
        """주소를 좌표로 변환한다.

        MVP 스텁: 실제 API 호출을 하지 않고 항상 (None, None)을 반환한다.
        API 키가 설정되어 있어도 실제 지오코딩 로직은 후속 작업에서 구현한다.
        """
        if not address or not self.is_enabled:
            return GeocodeResult(latitude=None, longitude=None)

        # TODO: 카카오/네이버 지오코딩 API 실제 연동 (후순위, 지시서 §1)
        return GeocodeResult(latitude=None, longitude=None)


geocoding_service = GeocodingService()
