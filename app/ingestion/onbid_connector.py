"""온비드(OnBid) 실제 Connector.

공공데이터포털(data.go.kr)에서 제공하는 "차세대 온비드" 계열 Open API 2개를 사용해
공매 물건 목록/상세를 조회하고, 지시서 §9.3 정규화 형태(dict)로 변환한다.

- 제공기관: 한국자산관리공사(캠코, KAMCO) — 공공데이터포털(data.go.kr) 경유로 제공
- 물건목록 신청/문서 페이지: https://www.data.go.kr/data/15157207/openapi.do
  ("한국자산관리공사_차세대 온비드 부동산 물건목록 조회서비스", OnbidRlstListSrvc2)
  Base URL: https://apis.data.go.kr/B010003/OnbidRlstListSrvc2
  오퍼레이션: getRlstCltrList2
  필수 파라미터: prptDivCd(재산유형코드), pvctTrgtYn(수의계약가능여부)
- 물건상세 신청/문서 페이지: https://www.data.go.kr/data/15157251/openapi.do
  ("한국자산관리공사_차세대 온비드 물건상세 입찰정보 조회서비스", OnbidCltrBidDtlSrvc2)
  Base URL: https://apis.data.go.kr/B010003/OnbidCltrBidDtlSrvc2
  오퍼레이션: getCltrBidInf2
  필수 파라미터: cltrMngNo(물건관리번호), pbctCdtnNo(공매조건번호) — 물건목록 응답에서 얻는다.
- 인증 방식: data.go.kr에서 발급받은 서비스키(계정당 1개, 두 API 공통)를 `serviceKey`
  쿼리 파라미터로 전달 (개발계정 트래픽 1,000회/일)
- 응답 형식: XML (공공데이터포털 표준 openapi 스키마 - response/header/body/items/item)

주의: 예전에는 "온비드 캠코공매물건 조회서비스"(data.go.kr/data/15000851, 오퍼레이션
getKamcoPbctCltrList)를 참조해 구현했으나, 해당 데이터셋은 폐기되어 더 이상 존재하지
않는다. 2026-07-11 실제 서비스키로 위 "차세대" API 2개를 호출해 정상 응답을 확인하고
이 구현으로 교체했다.
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

ONBID_LIST_BASE_URL = "https://apis.data.go.kr/B010003/OnbidRlstListSrvc2"
ONBID_LIST_OPERATION = "getRlstCltrList2"
ONBID_DETAIL_BASE_URL = "https://apis.data.go.kr/B010003/OnbidCltrBidDtlSrvc2"
ONBID_DETAIL_OPERATION = "getCltrBidInf2"

# prptDivCd(재산유형코드) 전체 값(복수 요청은 쉼표로 구분). 필수 파라미터라 기본값으로
# 전체 유형을 지정해 별도 지정 없이도 폭넓게 조회되도록 한다.
DEFAULT_PRPT_DIV_CD = "0002,0003,0004,0005,0006,0007,0008,0010,0011,0013"
# pvctTrgtYn(수의계약가능여부) 필수 파라미터. 기본값은 일반(비수의계약) 물건.
DEFAULT_PVCT_TRGT_YN = "N"

# 물건목록 조회서비스는 한 번에 최대 numOfRows(기본 100)건만 내려준다. 전체
# 재산유형 기준 물건 수가 6만건대라(2026-07-11 실호출 기준 totalCount=64,440)
# fetch_items 1회 호출로 여러 페이지를 이어서 모아 커버리지를 넓힌다.
# ponytail: 매 호출이 항상 pageNo=1부터 시작해 매번 같은 구간(최대
# max_pages*numOfRows건)만 반복 조회한다 — 전체 카탈로그를 여러 번의 호출에
# 걸쳐 순회하는 회전 커서는 없다. 업그레이드하려면 마지막으로 조회한 페이지
# 번호를 Redis 등에 저장해 다음 호출이 이어서 시작하도록 만들면 된다.
DEFAULT_MAX_PAGES = 20

# cltrUsgLclsCtgrNm/cltrUsgMclsCtgrNm/cltrUsgSclsCtgrNm(용도 대/중/소분류명) 원문에
# 포함된 키워드 -> 내부 category 값 매핑.
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
    ("전", "land"),
    ("답", "land"),
    ("자동차", "vehicle"),
    ("차량", "vehicle"),
)


class OnbidConnectorConfigError(RuntimeError):
    """ONBID_API_KEY 등 필수 설정값이 없거나 필수 파라미터가 누락되었을 때 발생한다."""


class OnbidConnectorAPIError(RuntimeError):
    """온비드 Open API 호출 또는 응답 처리 중 오류가 발생했을 때 던진다."""


class OnbidConnector(BaseConnector):
    """온비드 공식 API(공공데이터포털 "차세대 온비드" 물건목록/물건상세) 연동 Connector."""

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

    async def _request(self, base_url: str, operation: str, params: dict[str, Any]) -> str:
        url = f"{base_url}/{operation}"
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
        """공매 물건(부동산) 목록을 조회해 정규화된 dict 목록으로 반환한다.

        kwargs로 prptDivCd/pvctTrgtYn/bidDivCd/dspsMthodCd/lctnSdnm/lctnSggnm/lctnEmdNm
        등 물건목록 조회서비스가 지원하는 검색 조건을 그대로 전달할 수 있다.
        prptDivCd, pvctTrgtYn은 필수 파라미터라 지정하지 않으면 기본값을 사용한다.

        numOfRows(기본 100)건씩 pageNo(기본 1부터)를 max_pages(기본
        DEFAULT_MAX_PAGES)회까지 순회하며 모은다. 응답 건수가 numOfRows보다
        적은 페이지를 만나면 더 뒤 페이지가 없다는 뜻이므로 그 지점에서 멈춘다.
        """
        kwargs = dict(kwargs)
        num_of_rows = kwargs.pop("numOfRows", 100)
        start_page = kwargs.pop("pageNo", 1)
        max_pages = kwargs.pop("max_pages", DEFAULT_MAX_PAGES)
        base_params: dict[str, Any] = {
            "numOfRows": num_of_rows,
            "resultType": "xml",
            "prptDivCd": kwargs.pop("prptDivCd", DEFAULT_PRPT_DIV_CD),
            "pvctTrgtYn": kwargs.pop("pvctTrgtYn", DEFAULT_PVCT_TRGT_YN),
        }
        base_params.update(kwargs)

        all_raw_items: list[dict[str, str]] = []
        for offset in range(max_pages):
            params = {**base_params, "pageNo": start_page + offset}
            xml_text = await self._request(ONBID_LIST_BASE_URL, ONBID_LIST_OPERATION, params)
            raw_items = self._parse_list_response(xml_text)
            if not raw_items:
                break
            all_raw_items.extend(raw_items)
            if len(raw_items) < num_of_rows:
                break

        return [self._normalize_list_item(raw) for raw in all_raw_items]

    async def fetch_detail(self, source_item_id: str) -> dict[str, Any]:
        """단일 물건의 입찰 상세 정보를 조회한다.

        source_item_id는 `fetch_items`가 반환하는
        "{cltrMngNo}::{pbctCdtnNo}" 형식을 그대로 사용한다
        (cltrMngNo 자체에 하이픈이 포함되므로 "-"가 아닌 "::"로 구분한다).
        """
        cltr_mng_no, pbct_cdtn_no = self._split_source_item_id(source_item_id)
        params: dict[str, Any] = {
            "numOfRows": 1,
            "pageNo": 1,
            "resultType": "xml",
            "cltrMngNo": cltr_mng_no,
            "pbctCdtnNo": pbct_cdtn_no,
        }

        xml_text = await self._request(ONBID_DETAIL_BASE_URL, ONBID_DETAIL_OPERATION, params)
        raw_items = self._parse_list_response(xml_text)
        if not raw_items:
            raise ValueError(f"Unknown source_item_id: {source_item_id}")
        return self._normalize_detail_item(raw_items[0])

    # -- 파싱 ----------------------------------------------------------------

    @staticmethod
    def _split_source_item_id(source_item_id: str) -> tuple[str, str]:
        if "::" not in source_item_id:
            raise ValueError(f"Unknown source_item_id: {source_item_id}")
        cltr_mng_no, _, pbct_cdtn_no = source_item_id.partition("::")
        return cltr_mng_no, pbct_cdtn_no

    @staticmethod
    def _parse_list_response(xml_text: str) -> list[dict[str, str]]:
        """공공데이터포털 표준 openapi XML 응답을 파싱한다.

        형태:
            <response>
              <header><resultCode>00</resultCode><resultMsg>NORMAL_CODE</resultMsg></header>
              <body><items><item>...</item>...</items><totalCount>N</totalCount></body>
            </response>

        resultCode가 정상(00/0/000)이 아니면 OnbidConnectorAPIError를 던진다.
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
            if result_code and result_code not in ("00", "0", "000"):
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
    def _normalize_list_item(cls, raw: dict[str, str]) -> dict[str, Any]:
        """물건목록(getRlstCltrList2) 응답 필드를 지시서 §9.3 정규화 dict로 변환한다.

        참고한 원본 필드: cltrMngNo(물건관리번호), pbctCdtnNo(공매조건번호),
        onbidPbancNo(온비드공고번호), pbctNsq(회차), onbidCltrNm(물건명),
        cltrUsgLclsCtgrNm/cltrUsgMclsCtgrNm/cltrUsgSclsCtgrNm(용도 대/중/소분류명),
        lctnSdnm/lctnSggnm/lctnEmdNm(소재지 시도/시군구/읍면동),
        apslEvlAmt(감정평가금액), lowstBidPrcIndctCont(최저입찰가격),
        cltrBidBgngDt(입찰시작일시), usbdNft(유찰횟수)
        """
        cltr_mng_no = raw.get("cltrMngNo", "")
        pbct_cdtn_no = raw.get("pbctCdtnNo", "")
        source_item_id = f"{cltr_mng_no}::{pbct_cdtn_no}"

        sido = raw.get("lctnSdnm", "")
        sigungu = raw.get("lctnSggnm", "")
        eupmyeondong = raw.get("lctnEmdNm", "")
        address = " ".join(part for part in (sido, sigungu, eupmyeondong) if part)

        category_source = " ".join(
            raw.get(key, "")
            for key in ("cltrUsgSclsCtgrNm", "cltrUsgMclsCtgrNm", "cltrUsgLclsCtgrNm")
        )

        return {
            "source": "onbid",
            "source_item_id": source_item_id,
            "auction_type": "public_sale",
            "case_number": raw.get("onbidPbancNo") or cltr_mng_no,
            "item_number": raw.get("pbctNsq") or "1",
            "category": cls._map_category(category_source),
            "title": raw.get("onbidCltrNm", ""),
            "address": address,
            "sido": sido,
            "sigungu": sigungu,
            "appraisal_price": cls._to_int(raw.get("apslEvlAmt")),
            "minimum_price": cls._to_int(raw.get("lowstBidPrcIndctCont")),
            "deposit_price": None,
            "bid_date": cls._to_isoformat(raw.get("cltrBidBgngDt")),
            "fail_count": cls._to_int(raw.get("usbdNft")) or 0,
            "status": "active",
        }

    @classmethod
    def _normalize_detail_item(cls, raw: dict[str, str]) -> dict[str, Any]:
        """물건상세(getCltrBidInf2) 응답 필드를 지시서 §9.3 정규화 dict로 변환한다.

        이 오퍼레이션은 용도/소재지/감정가 등 목록 조회 전용 필드를 내려주지 않으므로,
        입찰 관련 필드(공고명, 입찰기간, 유찰횟수 등) 위주로 채우고 나머지는 목록
        조회 결과와 병합해서 사용하는 것을 전제로 한다.
        """
        cltr_mng_no = raw.get("cltrMngNo", "")
        pbct_cdtn_no = raw.get("pbctCdtnNo", "")
        source_item_id = f"{cltr_mng_no}::{pbct_cdtn_no}"

        return {
            "source": "onbid",
            "source_item_id": source_item_id,
            "auction_type": "public_sale",
            "case_number": raw.get("onbidPbancNo") or cltr_mng_no,
            "item_number": raw.get("pbctNsq") or "1",
            "category": "unknown",
            "title": raw.get("onbidCltrNm", ""),
            "address": "",
            "sido": "",
            "sigungu": "",
            "appraisal_price": None,
            "minimum_price": None,
            "deposit_price": None,
            "bid_date": cls._to_isoformat(raw.get("cltrBidBgngDt")),
            "fail_count": cls._to_int(raw.get("usbdNft")) or 0,
            "status": "active",
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
        """온비드 일시 포맷(yyyyMMddHHmm 등)을 ISO 8601로 변환한다."""
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
    def _map_category(category_source: str) -> str:
        for keyword, category in _CATEGORY_KEYWORD_MAP:
            if keyword in category_source:
                return category
        return "unknown"
