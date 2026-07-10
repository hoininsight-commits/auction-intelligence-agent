"""온비드(OnBid) 실제 Connector.

공공데이터포털(data.go.kr)에서 제공하는
"한국자산관리공사_온비드 캠코공매물건 조회서비스" Open API를 사용해
공매 물건 목록/상세를 조회하고, 지시서 §9.3 정규화 형태(dict)로 변환한다.

- 제공기관: 한국자산관리공사(캠코, KAMCO) — 공공데이터포털(data.go.kr) 경유로 제공
- 신청/문서 페이지: https://www.data.go.kr/data/15000851/openapi.do
  ("한국자산관리공사_온비드 캠코공매물건 조회서비스")
- 서비스 Base URL: http://openapi.onbid.co.kr/openapi/services/KamcoPblsalThingInquireSvc
- 주요 오퍼레이션: getKamcoPbctCltrList (물건목록 조회, 공고번호/공매번호로 필터링해
  상세 조회 용도로도 사용 가능)
- 인증 방식: data.go.kr에서 "일반 인증키(Encoding)"를 발급받아 `serviceKey` 쿼리
  파라미터로 전달 (개발계정 트래픽 1,000회/일, 운영 전환 시 증량 신청 가능)
- 응답 형식: XML (공공데이터포털 표준 openapi 스키마 - response/header/body/items/item)

주의: 이 구현은 실제 서비스키를 발급받지 못한 상태에서, data.go.kr 카탈로그 설명 및
공개된 API 가이드(PublicDataReader 오픈소스 프로젝트의 Kamco 문서)를 근거로 작성했다.
실제 연동 전에는 data.go.kr에서 최신 요청/응답 명세(특히 필드명)를 반드시 재확인해야 한다.
"""
from __future__ import annotations

from datetime import datetime
from typing import Any
from xml.etree import ElementTree as ET

import httpx

from app.core.config import settings
from app.core.logging import get_logger
from app.ingestion.base import BaseConnector

logger = get_logger(__name__)

ONBID_BASE_URL = "http://openapi.onbid.co.kr/openapi/services/KamcoPblsalThingInquireSvc"
ONBID_LIST_OPERATION = "getKamcoPbctCltrList"

# 처분방식코드(DPSL_MTD_CD): 0001=매각, 0002=임대(대부). 공매 검색 기본값은 매각.
DEFAULT_DPSL_MTD_CD = "0001"

# CTGR_FULL_NM(용도명) 원문에 포함된 키워드 -> 내부 category 값 매핑.
# (mock_onbid_connector.py가 사용하는 category 값과 동일한 어휘를 사용한다.)
_CATEGORY_KEYWORD_MAP: tuple[tuple[str, str], ...] = (
    ("아파트", "apartment"),
    ("오피스텔", "officetel"),
    ("단독", "house"),
    ("다세대", "house"),
    ("연립", "house"),
    ("상가", "commercial"),
    ("업무", "commercial"),
    ("근린", "commercial"),
    ("공장", "factory"),
    ("토지", "land"),
    ("임야", "land"),
    ("대지", "land"),
    ("자동차", "vehicle"),
    ("차량", "vehicle"),
)


class OnbidConnectorConfigError(RuntimeError):
    """ONBID_API_KEY 등 필수 설정값이 없을 때 발생한다."""


class OnbidConnectorAPIError(RuntimeError):
    """온비드 Open API 호출 또는 응답 처리 중 오류가 발생했을 때 던진다."""


class OnbidConnector(BaseConnector):
    """온비드 공식 API(공공데이터포털 캠코공매물건 조회서비스) 연동 Connector."""

    source = "onbid"

    def __init__(self) -> None:
        if not settings.ONBID_API_KEY:
            raise OnbidConnectorConfigError(
                "ONBID_API_KEY가 설정되지 않았습니다. 실제 온비드 API 연동을 사용하려면 "
                ".env에 ONBID_API_KEY를 설정하거나, ENABLE_MOCK_CONNECTORS=true로 "
                "MockOnbidConnector를 사용하세요."
            )
        self.api_key = settings.ONBID_API_KEY

    # -- HTTP 호출 ---------------------------------------------------------

    async def _request(self, operation: str, params: dict[str, Any]) -> str:
        url = f"{ONBID_BASE_URL}/{operation}"
        query: dict[str, Any] = {"serviceKey": self.api_key, **params}
        try:
            async with httpx.AsyncClient(timeout=15.0) as client:
                response = await client.get(url, params=query)
                response.raise_for_status()
                return response.text
        except httpx.HTTPError as exc:
            raise OnbidConnectorAPIError(
                f"온비드 API 호출에 실패했습니다 ({operation}): {exc}"
            ) from exc

    # -- BaseConnector 구현 --------------------------------------------------

    async def fetch_items(self, **kwargs) -> list[dict[str, Any]]:
        """공매 물건 목록을 조회해 정규화된 dict 목록으로 반환한다.

        kwargs로 SIDO/SGK/EMD/CTGR_HIRK_ID/DPSL_MTD_CD/numOfRows/pageNo 등
        온비드 API가 지원하는 검색 조건을 그대로 전달할 수 있다.
        """
        params: dict[str, Any] = {
            "numOfRows": kwargs.pop("numOfRows", 100),
            "pageNo": kwargs.pop("pageNo", 1),
            "DPSL_MTD_CD": kwargs.pop("DPSL_MTD_CD", DEFAULT_DPSL_MTD_CD),
        }
        params.update(kwargs)

        xml_text = await self._request(ONBID_LIST_OPERATION, params)
        raw_items = self._parse_list_response(xml_text)
        return [self._normalize_item(raw) for raw in raw_items]

    async def fetch_detail(self, source_item_id: str) -> dict[str, Any]:
        """단일 물건 상세를 조회한다.

        온비드 API는 별도의 전용 "물건상세" 오퍼레이션명이 문서 확인이 어려워,
        목록 조회 오퍼레이션을 공고번호(PLNM_NO)/공매번호(PBCT_NO)로 좁혀서
        단건을 찾아내는 방식으로 구현했다. source_item_id는
        `fetch_items`가 반환한 "{PLNM_NO}-{PBCT_NO}" 형식을 그대로 사용한다.
        """
        plnm_no, pbct_no = self._split_source_item_id(source_item_id)
        params: dict[str, Any] = {
            "numOfRows": 10,
            "pageNo": 1,
            "PLNM_NO": plnm_no,
        }
        if pbct_no:
            params["PBCT_NO"] = pbct_no

        xml_text = await self._request(ONBID_LIST_OPERATION, params)
        raw_items = self._parse_list_response(xml_text)

        for raw in raw_items:
            normalized = self._normalize_item(raw)
            if normalized["source_item_id"] == source_item_id:
                return normalized

        raise ValueError(f"Unknown source_item_id: {source_item_id}")

    # -- 파싱 ----------------------------------------------------------------

    @staticmethod
    def _split_source_item_id(source_item_id: str) -> tuple[str, str | None]:
        if "-" in source_item_id:
            plnm_no, _, pbct_no = source_item_id.partition("-")
            return plnm_no, pbct_no or None
        return source_item_id, None

    @staticmethod
    def _parse_list_response(xml_text: str) -> list[dict[str, str]]:
        """공공데이터포털 표준 openapi XML 응답을 파싱한다.

        형태:
            <response>
              <header><resultCode>00</resultCode><resultMsg>OK</resultMsg></header>
              <body><items><item>...</item>...</items><totalCount>N</totalCount></body>
            </response>

        resultCode가 정상(00/0)이 아니면 OnbidConnectorAPIError를 던진다.
        """
        try:
            root = ET.fromstring(xml_text)
        except ET.ParseError as exc:
            raise OnbidConnectorAPIError(
                f"온비드 API 응답을 XML로 파싱할 수 없습니다: {exc}"
            ) from exc

        header = root.find(".//header")
        if header is not None:
            result_code = (header.findtext("resultCode") or "").strip()
            result_msg = (header.findtext("resultMsg") or "").strip()
            if result_code and result_code not in ("00", "0"):
                raise OnbidConnectorAPIError(
                    f"온비드 API가 오류를 반환했습니다: [{result_code}] {result_msg}"
                )

        items: list[dict[str, str]] = []
        for item_el in root.findall(".//items/item"):
            item: dict[str, str] = {}
            for field in item_el:
                if field.tag and field.text is not None:
                    item[field.tag] = field.text.strip()
            items.append(item)
        return items

    # -- 정규화 (지시서 §9.3) --------------------------------------------------

    @classmethod
    def _normalize_item(cls, raw: dict[str, str]) -> dict[str, Any]:
        """온비드 원본 필드를 지시서 §9.3 정규화 dict 형태로 변환한다.

        참고한 온비드 원본 필드(캠코공매물건 조회서비스 명세, 공개 가이드 기준):
            PLNM_NO(공고번호), PBCT_NO(공매번호), CLTR_NM(물건명),
            CTGR_FULL_NM(용도명), MIN_BID_PRC(최저입찰가),
            APSL_ASES_AVG_AMT(감정가), BID_GRT_AMT(입찰보증금),
            PBCT_CLTR_STAT_NM(물건상태), USCBD_CNT(유찰횟수),
            PBCT_BEGN_DTM(입찰시작일시), LDNM_ADRS/NMRD_ADRS(지번/도로명주소),
            SIDO_NM/SGK_NM(시도/시군구명)
        """
        plnm_no = raw.get("PLNM_NO", "")
        pbct_no = raw.get("PBCT_NO", "")
        source_item_id = f"{plnm_no}-{pbct_no}" if pbct_no else plnm_no

        address = raw.get("NMRD_ADRS") or raw.get("LDNM_ADRS") or raw.get("PBCT_ADRS") or ""
        sido = raw.get("SIDO_NM") or raw.get("SIDO") or ""
        sigungu = raw.get("SGK_NM") or raw.get("SGK") or ""

        minimum_price = cls._to_int(raw.get("MIN_BID_PRC"))
        deposit_price = cls._to_int(raw.get("BID_GRT_AMT"))

        return {
            "source": "onbid",
            "source_item_id": source_item_id,
            "auction_type": "public_sale",
            "case_number": plnm_no or source_item_id,
            "item_number": pbct_no or "1",
            "category": cls._map_category(raw.get("CTGR_FULL_NM", "")),
            "title": raw.get("CLTR_NM", ""),
            "address": address,
            "sido": sido,
            "sigungu": sigungu,
            "appraisal_price": cls._to_int(raw.get("APSL_ASES_AVG_AMT")),
            "minimum_price": minimum_price,
            "deposit_price": deposit_price,
            "bid_date": cls._to_isoformat(raw.get("PBCT_BEGN_DTM")),
            "fail_count": cls._to_int(raw.get("USCBD_CNT")) or 0,
            "status": cls._map_status(raw.get("PBCT_CLTR_STAT_NM", "")),
        }

    @staticmethod
    def _to_int(value: str | None) -> int | None:
        if value is None or value == "":
            return None
        try:
            return int(float(value))
        except (TypeError, ValueError):
            return None

    @staticmethod
    def _to_isoformat(value: str | None) -> str | None:
        """온비드 일시 포맷(YYYYMMDDHH24MISS 또는 YYYYMMDD)을 ISO 8601로 변환한다."""
        if not value:
            return None
        value = value.strip()
        for fmt in ("%Y%m%d%H%M%S", "%Y%m%d%H%M", "%Y%m%d"):
            try:
                return datetime.strptime(value, fmt).isoformat()
            except ValueError:
                continue
        # 이미 ISO 형식이거나 알 수 없는 포맷이면 원본을 그대로 둔다.
        return value

    @staticmethod
    def _map_category(ctgr_full_nm: str) -> str:
        for keyword, category in _CATEGORY_KEYWORD_MAP:
            if keyword in ctgr_full_nm:
                return category
        return ctgr_full_nm or "unknown"

    @staticmethod
    def _map_status(pbct_cltr_stat_nm: str) -> str:
        stat = pbct_cltr_stat_nm.strip()
        if not stat:
            return "unknown"
        if "취소" in stat or "종료" in stat or "낙찰" in stat or "마감" in stat:
            return "closed"
        if "진행" in stat or "입찰중" in stat or "공고중" in stat:
            return "active"
        return stat
