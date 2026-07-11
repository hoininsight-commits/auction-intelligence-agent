"""국토교통부 실거래가 실제 Connector.

공공데이터포털(data.go.kr)에서 제공하는
"국토교통부_아파트 매매 실거래가 상세 자료" Open API를 사용해
아파트 매매 실거래 내역을 조회하고, 지시서 §9.4 정규화 형태(dict)로 변환한다.

- 제공기관: 국토교통부 — 공공데이터포털(data.go.kr) 경유로 제공
- 신청/문서 페이지: https://www.data.go.kr/data/15126468/openapi.do
  ("국토교통부_아파트 매매 실거래가 상세 자료")
- 서비스 Base URL: https://apis.data.go.kr/1613000/RTMSDataSvcAptTradeDev
- 오퍼레이션: getRTMSDataSvcAptTradeDev
- 인증 방식: data.go.kr에서 "일반 인증키(Decoding)"를 발급받아 `serviceKey` 쿼리
  파라미터로 전달 (개발/운영 계정 모두 자동승인, 개발계정 트래픽 10,000회/일)
- 필수 요청 파라미터: LAWD_CD(법정동시군구코드 5자리), DEAL_YMD(계약년월 YYYYMM 6자리)
  (선택: pageNo, numOfRows)
- 응답 형식: XML (공공데이터포털 표준 openapi 스키마 - response/header/body/items/item)

주요 응답 필드(아파트 매매 실거래가 상세 자료, 공개된 API 가이드 기준):
    aptNm(단지명), umdNm(법정동/읍면동명), jibun(지번), roadNm(도로명),
    excluUseAr(전용면적, m^2), dealAmount(거래금액, "만원" 단위 문자열 - 쉼표 포함),
    dealYear/dealMonth/dealDay(계약년/월/일), floor(층), buildYear(건축년도),
    sggCd(시군구코드)

2026-07-11 실제 서비스키로 호출해 정상 응답(XML, resultCode 000/OK)을 확인했다.

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

MOLIT_BASE_URL = "https://apis.data.go.kr/1613000/RTMSDataSvcAptTradeDev"
MOLIT_OPERATION = "getRTMSDataSvcAptTradeDev"

# 시군구명 -> 법정동시군구코드(LAWD_CD, 5자리) 매핑 테이블. 전국 시/군/구 단위로
# 확장되어 있다(출처: 행정표준코드관리시스템 www.code.go.kr 법정동코드 앞 5자리,
# 2023년 대구광역시 군위군 편입 등 최신 개편 반영). 매핑에 없는 지역(신설/통합 등으로
# 누락되었을 수 있음)은 명확한 에러를 던져 호출자가 LAWD_CD를 직접 지정하도록 유도한다.
# 실제 서비스키로 호출하기 전에는 data.go.kr 최신 법정동코드 자료로 재검증 권장.
_LAWD_CD_MAP: dict[str, str] = {
    # 서울특별시
    "서울특별시 종로구": "11110",
    "서울특별시 중구": "11140",
    "서울특별시 용산구": "11170",
    "서울특별시 성동구": "11200",
    "서울특별시 광진구": "11215",
    "서울특별시 동대문구": "11230",
    "서울특별시 중랑구": "11260",
    "서울특별시 성북구": "11290",
    "서울특별시 강북구": "11305",
    "서울특별시 도봉구": "11320",
    "서울특별시 노원구": "11350",
    "서울특별시 은평구": "11380",
    "서울특별시 서대문구": "11410",
    "서울특별시 마포구": "11440",
    "서울특별시 양천구": "11470",
    "서울특별시 강서구": "11500",
    "서울특별시 구로구": "11530",
    "서울특별시 금천구": "11545",
    "서울특별시 영등포구": "11560",
    "서울특별시 동작구": "11590",
    "서울특별시 관악구": "11620",
    "서울특별시 서초구": "11650",
    "서울특별시 강남구": "11680",
    "서울특별시 송파구": "11710",
    "서울특별시 강동구": "11740",
    # 부산광역시
    "부산광역시 중구": "26110",
    "부산광역시 서구": "26140",
    "부산광역시 동구": "26170",
    "부산광역시 영도구": "26200",
    "부산광역시 부산진구": "26230",
    "부산광역시 동래구": "26260",
    "부산광역시 남구": "26290",
    "부산광역시 북구": "26320",
    "부산광역시 해운대구": "26350",
    "부산광역시 사하구": "26380",
    "부산광역시 금정구": "26410",
    "부산광역시 강서구": "26440",
    "부산광역시 연제구": "26470",
    "부산광역시 수영구": "26500",
    "부산광역시 사상구": "26530",
    "부산광역시 기장군": "26710",
    # 대구광역시
    "대구광역시 중구": "27110",
    "대구광역시 동구": "27140",
    "대구광역시 서구": "27170",
    "대구광역시 남구": "27200",
    "대구광역시 북구": "27230",
    "대구광역시 수성구": "27260",
    "대구광역시 달서구": "27290",
    "대구광역시 달성군": "27710",
    "대구광역시 군위군": "27720",
    # 인천광역시
    "인천광역시 중구": "28110",
    "인천광역시 동구": "28140",
    "인천광역시 미추홀구": "28177",
    "인천광역시 연수구": "28185",
    "인천광역시 남동구": "28200",
    "인천광역시 부평구": "28237",
    "인천광역시 계양구": "28245",
    "인천광역시 서구": "28260",
    "인천광역시 강화군": "28710",
    "인천광역시 옹진군": "28720",
    # 광주광역시
    "광주광역시 동구": "29110",
    "광주광역시 서구": "29140",
    "광주광역시 남구": "29155",
    "광주광역시 북구": "29170",
    "광주광역시 광산구": "29200",
    # 대전광역시
    "대전광역시 동구": "30110",
    "대전광역시 중구": "30140",
    "대전광역시 서구": "30170",
    "대전광역시 유성구": "30200",
    "대전광역시 대덕구": "30230",
    # 울산광역시
    "울산광역시 중구": "31110",
    "울산광역시 남구": "31140",
    "울산광역시 동구": "31170",
    "울산광역시 북구": "31200",
    "울산광역시 울주군": "31710",
    # 세종특별자치시 (구/군 구분 없는 단일 행정구역)
    "세종특별자치시": "36110",
    # 경기도
    "경기도 수원시장안구": "41111",
    "경기도 수원시권선구": "41113",
    "경기도 수원시팔달구": "41115",
    "경기도 수원시영통구": "41117",
    "경기도 성남시수정구": "41131",
    "경기도 성남시중원구": "41133",
    "경기도 성남시분당구": "41135",
    "경기도 의정부시": "41150",
    "경기도 안양시만안구": "41171",
    "경기도 안양시동안구": "41173",
    "경기도 부천시": "41190",
    "경기도 광명시": "41210",
    "경기도 평택시": "41220",
    "경기도 동두천시": "41250",
    "경기도 안산시상록구": "41271",
    "경기도 안산시단원구": "41273",
    "경기도 고양시덕양구": "41281",
    "경기도 고양시일산동구": "41285",
    "경기도 고양시일산서구": "41287",
    "경기도 과천시": "41290",
    "경기도 구리시": "41310",
    "경기도 남양주시": "41360",
    "경기도 오산시": "41370",
    "경기도 시흥시": "41390",
    "경기도 군포시": "41410",
    "경기도 의왕시": "41430",
    "경기도 하남시": "41450",
    "경기도 용인시처인구": "41461",
    "경기도 용인시기흥구": "41463",
    "경기도 용인시수지구": "41465",
    "경기도 파주시": "41480",
    "경기도 이천시": "41500",
    "경기도 안성시": "41550",
    "경기도 김포시": "41570",
    "경기도 화성시": "41590",
    "경기도 광주시": "41610",
    "경기도 양주시": "41630",
    "경기도 포천시": "41650",
    "경기도 여주시": "41670",
    "경기도 연천군": "41800",
    "경기도 가평군": "41820",
    "경기도 양평군": "41830",
    # 강원특별자치도
    "강원특별자치도 춘천시": "42110",
    "강원특별자치도 원주시": "42130",
    "강원특별자치도 강릉시": "42150",
    "강원특별자치도 동해시": "42170",
    "강원특별자치도 태백시": "42190",
    "강원특별자치도 속초시": "42210",
    "강원특별자치도 삼척시": "42230",
    "강원특별자치도 홍천군": "42720",
    "강원특별자치도 횡성군": "42730",
    "강원특별자치도 영월군": "42750",
    "강원특별자치도 평창군": "42760",
    "강원특별자치도 정선군": "42770",
    "강원특별자치도 철원군": "42780",
    "강원특별자치도 화천군": "42790",
    "강원특별자치도 양구군": "42800",
    "강원특별자치도 인제군": "42810",
    "강원특별자치도 고성군": "42820",
    "강원특별자치도 양양군": "42830",
    # 충청북도
    "충청북도 청주시상당구": "43111",
    "충청북도 청주시서원구": "43112",
    "충청북도 청주시흥덕구": "43113",
    "충청북도 청주시청원구": "43114",
    "충청북도 충주시": "43130",
    "충청북도 제천시": "43150",
    "충청북도 보은군": "43720",
    "충청북도 옥천군": "43730",
    "충청북도 영동군": "43740",
    "충청북도 증평군": "43745",
    "충청북도 진천군": "43750",
    "충청북도 괴산군": "43760",
    "충청북도 음성군": "43770",
    "충청북도 단양군": "43800",
    # 충청남도
    "충청남도 천안시동남구": "44131",
    "충청남도 천안시서북구": "44133",
    "충청남도 공주시": "44150",
    "충청남도 보령시": "44180",
    "충청남도 아산시": "44200",
    "충청남도 서산시": "44210",
    "충청남도 논산시": "44230",
    "충청남도 계룡시": "44250",
    "충청남도 당진시": "44270",
    "충청남도 금산군": "44710",
    "충청남도 부여군": "44760",
    "충청남도 서천군": "44770",
    "충청남도 청양군": "44790",
    "충청남도 홍성군": "44800",
    "충청남도 예산군": "44810",
    "충청남도 태안군": "44825",
    # 전북특별자치도
    "전북특별자치도 전주시완산구": "45111",
    "전북특별자치도 전주시덕진구": "45113",
    "전북특별자치도 군산시": "45130",
    "전북특별자치도 익산시": "45140",
    "전북특별자치도 정읍시": "45180",
    "전북특별자치도 남원시": "45190",
    "전북특별자치도 김제시": "45210",
    "전북특별자치도 완주군": "45710",
    "전북특별자치도 진안군": "45720",
    "전북특별자치도 무주군": "45730",
    "전북특별자치도 장수군": "45740",
    "전북특별자치도 임실군": "45750",
    "전북특별자치도 순창군": "45770",
    "전북특별자치도 고창군": "45790",
    "전북특별자치도 부안군": "45800",
    # 전라남도
    "전라남도 목포시": "46110",
    "전라남도 여수시": "46130",
    "전라남도 순천시": "46150",
    "전라남도 나주시": "46170",
    "전라남도 광양시": "46230",
    "전라남도 담양군": "46710",
    "전라남도 곡성군": "46720",
    "전라남도 구례군": "46730",
    "전라남도 고흥군": "46770",
    "전라남도 보성군": "46780",
    "전라남도 화순군": "46790",
    "전라남도 장흥군": "46800",
    "전라남도 강진군": "46810",
    "전라남도 해남군": "46820",
    "전라남도 영암군": "46830",
    "전라남도 무안군": "46840",
    "전라남도 함평군": "46860",
    "전라남도 영광군": "46870",
    "전라남도 장성군": "46880",
    "전라남도 완도군": "46890",
    "전라남도 진도군": "46900",
    "전라남도 신안군": "46910",
    # 경상북도
    "경상북도 포항시남구": "47111",
    "경상북도 포항시북구": "47113",
    "경상북도 경주시": "47130",
    "경상북도 김천시": "47150",
    "경상북도 안동시": "47170",
    "경상북도 구미시": "47190",
    "경상북도 영주시": "47210",
    "경상북도 영천시": "47230",
    "경상북도 상주시": "47250",
    "경상북도 문경시": "47280",
    "경상북도 경산시": "47290",
    "경상북도 의성군": "47730",
    "경상북도 청송군": "47750",
    "경상북도 영양군": "47760",
    "경상북도 영덕군": "47770",
    "경상북도 청도군": "47820",
    "경상북도 고령군": "47830",
    "경상북도 성주군": "47840",
    "경상북도 칠곡군": "47850",
    "경상북도 예천군": "47900",
    "경상북도 봉화군": "47920",
    "경상북도 울진군": "47930",
    "경상북도 울릉군": "47940",
    # 경상남도
    "경상남도 창원시의창구": "48121",
    "경상남도 창원시성산구": "48123",
    "경상남도 창원시마산합포구": "48125",
    "경상남도 창원시마산회원구": "48127",
    "경상남도 창원시진해구": "48129",
    "경상남도 진주시": "48170",
    "경상남도 통영시": "48220",
    "경상남도 사천시": "48240",
    "경상남도 김해시": "48250",
    "경상남도 밀양시": "48270",
    "경상남도 거제시": "48310",
    "경상남도 양산시": "48330",
    "경상남도 의령군": "48720",
    "경상남도 함안군": "48730",
    "경상남도 창녕군": "48740",
    "경상남도 고성군": "48750",
    "경상남도 남해군": "48760",
    "경상남도 하동군": "48770",
    "경상남도 산청군": "48780",
    "경상남도 함양군": "48800",
    "경상남도 거창군": "48810",
    "경상남도 합천군": "48820",
    # 제주특별자치도
    "제주특별자치도 제주시": "50110",
    "제주특별자치도 서귀포시": "50130",
}


def get_supported_regions() -> list[tuple[str, str]]:
    """`_LAWD_CD_MAP`에 등록된 전국 시/군/구를 (sido, sigungu) 튜플 목록으로 반환한다.

    전국 순회 수집(예: 매일 전체 지역을 돌며 실거래가를 갱신하는 배치 작업)에서
    반복 대상 지역 목록을 얻는 용도로 사용한다. 세종특별자치시처럼 구/군 구분이
    없는 지역은 sigungu가 빈 문자열이다.
    """
    regions: list[tuple[str, str]] = []
    for key in _LAWD_CD_MAP:
        if " " in key:
            sido, sigungu = key.split(" ", 1)
        else:
            sido, sigungu = key, ""
        regions.append((sido, sigungu))
    return regions


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
        elif sido and sido in _LAWD_CD_MAP:
            # 세종특별자치시처럼 구/군 구분이 없어 sido 자체가 매핑 키인 경우.
            return _LAWD_CD_MAP[sido], sido, ""

        raise RealTransactionConnectorConfigError(
            "LAWD_CD(법정동시군구코드)를 확인할 수 없습니다. fetch_items(lawd_cd=...)로 "
            "직접 지정하거나, sido/sigungu가 내부 매핑 테이블(_LAWD_CD_MAP, 전국 시/군/구 "
            f"{len(_LAWD_CD_MAP)}개 등록)에 등록된 지역명과 정확히 일치하는지 확인하세요. "
            f"(sido={sido!r}, sigungu={sigungu!r})"
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

        참고한 원본 필드(아파트 매매 실거래가 상세 자료 API 가이드 기준):
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
