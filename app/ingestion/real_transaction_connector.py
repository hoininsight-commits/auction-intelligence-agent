"""국토교통부 실거래가 실제 Connector.

공공데이터포털(data.go.kr)에서 제공하는
"국토교통부_아파트 매매 실거래상세 자료" Open API를 사용해
아파트 매매 실거래 내역을 조회하고, 지시서 §9.4 정규화 형태(dict)로 변환한다.

- 제공기관: 국토교통부 — 공공데이터포털(data.go.kr) 경유로 제공
- 신청/문서 페이지: https://www.data.go.kr/data/15126468/openapi.do
  ("국토교통부_아파트 매매 실거래상세 자료")
- 서비스 Base URL: http://apis.data.go.kr/1613000/RTMSDataSvcAptTradeDev
- 오퍼레이션: getRTMSDataSvcAptTradeDev
- 인증 방식: data.go.kr에서 "일반 인증키(Decoding)"를 발급받아 `serviceKey` 쿼리
  파라미터로 전달 (개발/운영 계정 모두 자동승인, 개발계정 트래픽 10,000회/일)
- 필수 요청 파라미터: LAWD_CD(법정동시군구코드 5자리), DEAL_YMD(계약년월 YYYYMM 6자리)
  (선택: pageNo, numOfRows)
- 응답 형식: XML (공공데이터포털 표준 openapi 스키마 - response/header/body/items/item)

주요 응답 필드(아파트 매매 실거래상세 자료, 공개된 API 가이드 기준):
    aptNm(단지명), umdNm(법정동/읍면동명), jibun(지번), roadNm(도로명),
    excluUseAr(전용면적, m^2), dealAmount(거래금액, "만원" 단위 문자열 - 쉼표 포함),
    dealYear/dealMonth/dealDay(계약년/월/일), floor(층), buildYear(건축년도),
    sggCd(시군구코드)

주의: 이 구현은 실제 서비스키를 발급받지 못한 상태에서, data.go.kr 카탈로그 설명 및
공개된 API 가이드(PublicDataReader 오픈소스 프로젝트, 공공데이터 활용 블로그 등)를
근거로 작성했다. 실제 연동 전에는 data.go.kr에서 최신 요청/응답 명세를 반드시
재확인해야 한다.

아파트 외 매물종별(연립다세대/오피스텔/단독다가구 등)은 국토교통부가 각각 별도의
Open API 서비스로 제공한다(예: 연립다세대 매매 실거래가 자료, 오피스텔 매매
실거래가 자료). 이번 구현은 지시서 범위에 맞춰 아파트 매매 API만 다루며, 정규화
결과의 `property_type` 필드가 "apartment"로 고정된다. 추후 다른 매물종별 API를
추가할 때는 별도 Connector(또는 이 Connector의 오퍼레이션/파싱 로직 확장)로 대응하고
`property_type` 값만 바꿔 동일한 정규화 스키마(property_transactions 테이블)에
적재하면 된다.
"""
from __future__ import annotations

from datetime import date
from typing import Any
from xml.etree import ElementTree as ET

import httpx

from app.core.config import settings
from app.core.logging import get_logger
from app.ingestion.base import BaseConnector

logger = get_logger(__name__)

MOLIT_BASE_URL = "http://apis.data.go.kr/1613000/RTMSDataSvcAptTradeDev"
MOLIT_OPERATION = "getRTMSDataSvcAptTradeDev"

# 시군구명 -> 법정동시군구코드(LAWD_CD, 5자리) 최소 하드코딩 매핑 테이블.
# 전체 법정동코드 DB를 구축하는 대신, 자주 쓰이는 주요 시군구만 등록해 두고
# 매핑에 없는 지역은 명확한 에러를 던져 호출자가 LAWD_CD를 직접 지정하도록 유도한다.
# (출처: 행정표준코드관리시스템 www.code.go.kr 법정동코드 앞 5자리)
_LAWD_CD_MAP: dict[str, str] = {
    "서울특별시 강남구": "11680",
    "서울특별시 서초구": "11650",
    "서울특별시 송파구": "11710",
    "서울특별시 마포구": "11440",
    "서울특별시 종로구": "11110",
    "서울특별시 영등포구": "11560",
    "경기도 성남시분당구": "41135",
    "경기도 수원시영통구": "41117",
    "부산광역시 해운대구": "26350",
}


class RealTransactionConnectorConfigError(RuntimeError):
    """MOLIT_API_KEY 등 필수 설정값이 없거나 필수 파라미터가 누락되었을 때 발생한다."""


class RealTransactionConnectorAPIError(RuntimeError):
    """국토부 실거래가 Open API 호출 또는 응답 처리 중 오류가 발생했을 때 던진다."""


class RealTransactionConnector(BaseConnector):
    """국토부 아파트 매매 실거래가 공개 API(공공데이터포털) 연동 Connector."""

    source = "molit"

    def __init__(self) -> None:
        if not settings.MOLIT_API_KEY:
            raise RealTransactionConnectorConfigError(
                "MOLIT_API_KEY가 설정되지 않았습니다. 실제 국토부 실거래가 API 연동을 사용하려면 "
                ".env에 MOLIT_API_KEY를 설정하거나, ENABLE_MOCK_CONNECTORS=true로 "
                "MockRealTransactionConnector를 사용하세요."
            )
        self.api_key = settings.MOLIT_API_KEY

    # -- HTTP 호출 ---------------------------------------------------------

    async def _request(self, operation: str, params: dict[str, Any]) -> str:
        url = f"{MOLIT_BASE_URL}/{operation}"
        query: dict[str, Any] = {"serviceKey": self.api_key, **params}
        try:
            async with httpx.AsyncClient(timeout=15.0) as client:
                response = await client.get(url, params=query)
                response.raise_for_status()
                return response.text
        except httpx.HTTPError as exc:
            raise RealTransactionConnectorAPIError(
                f"국토부 실거래가 API 호출에 실패했습니다 ({operation}): {exc}"
            ) from exc

    # -- 파라미터 해석 --------------------------------------------------------

    @classmethod
    def _resolve_lawd_cd(cls, kwargs: dict[str, Any]) -> tuple[str, str, str]:
        """kwargs에서 LAWD_CD(법정동시군구코드)와 sido/sigungu 표시용 이름을 결정한다.

        국토부 실거래가 API 응답 자체에는 시도/시군구 "이름"이 내려오지 않으므로
        (sggCd 코드값만 제공), 정규화 결과의 sido/sigungu는 요청 시점에 결정해
        함께 반환한다.

        1) lawd_cd/LAWD_CD가 직접 주어지면 그대로 사용하고, sido/sigungu도 함께
           주어졌으면 그 값을 그대로 사용(없으면 빈 문자열).
        2) sido + sigungu(또는 sigungu 단독)가 주어지면 하드코딩 매핑 테이블에서
           LAWD_CD를 조회.
        3) 둘 다 없으면 config error.
        """
        lawd_cd = kwargs.pop("lawd_cd", None) or kwargs.pop("LAWD_CD", None)
        sido = kwargs.pop("sido", None) or ""
        sigungu = kwargs.pop("sigungu", None) or ""

        if lawd_cd:
            if not sido and not sigungu:
                # 매핑 테이블에 있으면 표시용 이름을 역으로 채워준다.
                for key, code in _LAWD_CD_MAP.items():
                    if code == str(lawd_cd):
                        sido, _, sigungu = key.partition(" ")
                        break
            return str(lawd_cd), sido, sigungu

        if sigungu:
            key = f"{sido} {sigungu}".strip() if sido else None
            if key and key in _LAWD_CD_MAP:
                return _LAWD_CD_MAP[key], sido, sigungu
            # sido 없이 시군구명만으로도 매핑 테이블에서 찾아본다.
            matches = [(k, v) for k, v in _LAWD_CD_MAP.items() if k.endswith(sigungu)]
            if len(matches) == 1:
                matched_key, matched_code = matches[0]
                matched_sido, _, matched_sigungu = matched_key.partition(" ")
                return matched_code, matched_sido, matched_sigungu

        raise RealTransactionConnectorConfigError(
            "LAWD_CD(법정동시군구코드)를 확인할 수 없습니다. fetch_items(lawd_cd=...)로 "
            "직접 지정하거나, sido/sigungu가 내부 매핑 테이블(_LAWD_CD_MAP)에 등록된 "
            "지역인지 확인하세요. 등록된 지역: " + ", ".join(sorted(_LAWD_CD_MAP))
        )

    @staticmethod
    def _resolve_deal_ymd(kwargs: dict[str, Any]) -> str:
        """kwargs에서 DEAL_YMD(계약년월, YYYYMM)를 결정한다. 없으면 이번 달을 기본값으로 사용."""
        deal_ymd = kwargs.pop("deal_ymd", None) or kwargs.pop("DEAL_YMD", None)
        if deal_ymd:
            return str(deal_ymd)
        today = date.today()
        return f"{today.year:04d}{today.month:02d}"

    # -- BaseConnector 구현 --------------------------------------------------

    async def fetch_items(self, **kwargs) -> list[dict[str, Any]]:
        """아파트 매매 실거래 내역을 조회해 정규화된 dict 목록으로 반환한다.

        kwargs:
            lawd_cd (또는 LAWD_CD): 법정동시군구코드(5자리). 직접 지정 가능.
            sido, sigungu: lawd_cd 미지정 시 내부 매핑 테이블로 LAWD_CD를 조회하는 데 사용.
            deal_ymd (또는 DEAL_YMD): 계약년월(YYYYMM, 6자리). 미지정 시 이번 달.
            numOfRows, pageNo: 페이지네이션 (기본 numOfRows=100, pageNo=1).
        """
        kwargs = dict(kwargs)
        lawd_cd, sido, sigungu = self._resolve_lawd_cd(kwargs)
        deal_ymd = self._resolve_deal_ymd(kwargs)

        params: dict[str, Any] = {
            "LAWD_CD": lawd_cd,
            "DEAL_YMD": deal_ymd,
            "numOfRows": kwargs.pop("numOfRows", 100),
            "pageNo": kwargs.pop("pageNo", 1),
        }
        params.update(kwargs)

        xml_text = await self._request(MOLIT_OPERATION, params)
        raw_items = self._parse_list_response(xml_text)
        return [self._normalize_item(raw, sido=sido, sigungu=sigungu) for raw in raw_items]

    async def fetch_detail(self, source_item_id: str) -> dict[str, Any]:
        """실거래가 데이터는 공식적으로 개별 상세 조회 개념이 없다.

        source_item_id는 `fetch_items`가 내부적으로 생성한 식별자
        (LAWD_CD-DEAL_YMD-index)를 기대하지만, 이 API는 건별 단건 조회를
        지원하지 않으므로 동일 조건으로 목록을 재조회해 인덱스로 찾아낸다.
        """
        try:
            lawd_cd, deal_ymd, idx_str = source_item_id.split("-")
            idx = int(idx_str)
        except ValueError as exc:
            raise ValueError(f"Unknown source_item_id: {source_item_id}") from exc

        items = await self.fetch_items(lawd_cd=lawd_cd, deal_ymd=deal_ymd, numOfRows=999)
        if 0 <= idx < len(items):
            return items[idx]
        raise ValueError(f"Unknown source_item_id: {source_item_id}")

    # -- 파싱 ----------------------------------------------------------------

    @staticmethod
    def _parse_list_response(xml_text: str) -> list[dict[str, str]]:
        """공공데이터포털 표준 openapi XML 응답을 파싱한다.

        형태:
            <response>
              <header><resultCode>00</resultCode><resultMsg>OK</resultMsg></header>
              <body><items><item>...</item>...</items><totalCount>N</totalCount></body>
            </response>

        resultCode가 정상(00/000)이 아니면 RealTransactionConnectorAPIError를 던진다.
        """
        try:
            root = ET.fromstring(xml_text)
        except ET.ParseError as exc:
            raise RealTransactionConnectorAPIError(
                f"국토부 실거래가 API 응답을 XML로 파싱할 수 없습니다: {exc}"
            ) from exc

        header = root.find(".//header")
        if header is not None:
            result_code = (header.findtext("resultCode") or "").strip()
            result_msg = (header.findtext("resultMsg") or "").strip()
            if result_code and result_code not in ("00", "0", "000"):
                raise RealTransactionConnectorAPIError(
                    f"국토부 실거래가 API가 오류를 반환했습니다: [{result_code}] {result_msg}"
                )

        items: list[dict[str, str]] = []
        for item_el in root.findall(".//items/item"):
            item: dict[str, str] = {}
            for field in item_el:
                if field.tag and field.text is not None:
                    item[field.tag] = field.text.strip()
            items.append(item)
        return items

    # -- 정규화 (지시서 §9.4) --------------------------------------------------

    @classmethod
    def _normalize_item(
        cls, raw: dict[str, str], *, sido: str = "", sigungu: str = ""
    ) -> dict[str, Any]:
        """국토부 원본 필드를 지시서 §9.4 정규화 dict 형태로 변환한다.

        참고한 원본 필드(아파트 매매 실거래상세 자료 API 가이드 기준):
            aptNm(단지명), umdNm(법정동/읍면동명), jibun(지번), roadNm(도로명),
            sggCd(시군구코드), excluUseAr(전용면적, m^2),
            dealAmount(거래금액, "만원" 단위 문자열 - 쉼표 포함), dealYear/dealMonth/dealDay,
            floor(층), buildYear(건축년도)
        """
        umd_nm = raw.get("umdNm", "")
        jibun = raw.get("jibun", "")
        road_nm = raw.get("roadNm", "")
        apt_nm = raw.get("aptNm", "")

        address_parts = [part for part in (umd_nm, jibun) if part]
        address = road_nm or " ".join(address_parts)

        deal_price = cls._parse_deal_amount(raw.get("dealAmount"))

        return {
            "property_type": "apartment",
            "address": address,
            "sido": sido,
            "sigungu": sigungu,
            "eupmyeondong": umd_nm,
            "complex_name": apt_nm,
            "exclusive_area": cls._to_float(raw.get("excluUseAr")),
            "deal_price": deal_price,
            "deal_year": cls._to_int(raw.get("dealYear")),
            "deal_month": cls._to_int(raw.get("dealMonth")),
            "deal_day": cls._to_int(raw.get("dealDay")),
            "floor_info": raw.get("floor", ""),
            "build_year": cls._to_int(raw.get("buildYear")),
            "source": "molit",
        }

    @staticmethod
    def _parse_deal_amount(value: str | None) -> int | None:
        """거래금액(dealAmount)은 "만원" 단위, 쉼표 포함 문자열(예: "105,000")로 내려온다.

        원(KRW) 단위 정수로 변환한다(105,000만원 -> 1,050,000,000원).
        """
        if value is None:
            return None
        cleaned = value.replace(",", "").strip()
        if not cleaned:
            return None
        try:
            return int(float(cleaned) * 10_000)
        except (TypeError, ValueError):
            return None

    @staticmethod
    def _to_int(value: str | None) -> int | None:
        if value is None or value == "":
            return None
        try:
            return int(float(value))
        except (TypeError, ValueError):
            return None

    @staticmethod
    def _to_float(value: str | None) -> float | None:
        if value is None or value == "":
            return None
        try:
            return float(value)
        except (TypeError, ValueError):
            return None
