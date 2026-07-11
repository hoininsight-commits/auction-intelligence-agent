"""온비드 페이지네이션 + 국토부 매물종별 정규화 로직 단위 테스트.

실제 네트워크 호출 없이(`_request`를 monkeypatch) 순수 로직만 검증한다.
"""

from __future__ import annotations

import pytest

from app.core.config import settings
from app.ingestion.onbid_connector import OnbidConnector
from app.ingestion.real_transaction_connector import (
    PROPERTY_TYPE_CONFIG,
    RealTransactionConnector,
    RealTransactionConnectorConfigError,
)


def _onbid_page_xml(count: int) -> str:
    items = "".join(
        f"<item><cltrMngNo>2026-{i:04d}</cltrMngNo><pbctCdtnNo>{i}</pbctCdtnNo>"
        f"<onbidCltrNm>샘플 물건 {i}</onbidCltrNm><apslEvlAmt>100000000</apslEvlAmt>"
        f"<lowstBidPrcIndctCont>80000000</lowstBidPrcIndctCont></item>"
        for i in range(count)
    )
    return (
        "<response><header><resultCode>00</resultCode><resultMsg>NORMAL_CODE</resultMsg>"
        f"</header><body><items>{items}</items><totalCount>999999</totalCount></body></response>"
    )


@pytest.fixture
def onbid_connector(monkeypatch: pytest.MonkeyPatch) -> OnbidConnector:
    monkeypatch.setattr(settings, "ONBID_API_KEY", "test-key")
    return OnbidConnector()


async def test_onbid_fetch_items_paginates_across_full_pages(
    onbid_connector: OnbidConnector, monkeypatch: pytest.MonkeyPatch
) -> None:
    """페이지마다 numOfRows(=2)만큼 꽉 채워 오면 max_pages까지 계속 다음 페이지를 요청한다."""
    calls: list[dict] = []

    async def fake_request(base_url, operation, params):
        calls.append(dict(params))
        return _onbid_page_xml(2)

    monkeypatch.setattr(onbid_connector, "_request", fake_request)

    items = await onbid_connector.fetch_items(numOfRows=2, max_pages=3)

    assert len(calls) == 3
    assert [c["pageNo"] for c in calls] == [1, 2, 3]
    assert len(items) == 6


async def test_onbid_fetch_items_stops_on_short_page(
    onbid_connector: OnbidConnector, monkeypatch: pytest.MonkeyPatch
) -> None:
    """응답 건수가 numOfRows보다 적은 페이지를 만나면 더 요청하지 않고 멈춘다."""
    calls: list[dict] = []

    async def fake_request(base_url, operation, params):
        calls.append(dict(params))
        return _onbid_page_xml(1)  # numOfRows=100인데 1건만 옴 -> 마지막 페이지

    monkeypatch.setattr(onbid_connector, "_request", fake_request)

    items = await onbid_connector.fetch_items(numOfRows=100, max_pages=20)

    assert len(calls) == 1
    assert len(items) == 1


async def test_onbid_fetch_items_stops_on_empty_page(
    onbid_connector: OnbidConnector, monkeypatch: pytest.MonkeyPatch
) -> None:
    async def fake_request(base_url, operation, params):
        return _onbid_page_xml(0)

    monkeypatch.setattr(onbid_connector, "_request", fake_request)

    items = await onbid_connector.fetch_items(numOfRows=100, max_pages=5)

    assert items == []


@pytest.fixture
def molit_connector(monkeypatch: pytest.MonkeyPatch) -> RealTransactionConnector:
    monkeypatch.setattr(settings, "MOLIT_API_KEY", "test-key")
    return RealTransactionConnector()


def test_molit_unknown_property_type_raises_config_error(
    molit_connector: RealTransactionConnector,
) -> None:
    with pytest.raises(RealTransactionConnectorConfigError):
        molit_connector._resolve_property_type_config({"property_type": "penthouse"})


@pytest.mark.parametrize(
    "property_type,raw,expected_name,expected_area,expected_floor",
    [
        (
            "apartment",
            {"aptNm": "샘플아파트", "excluUseAr": "84.5", "floor": "12"},
            "샘플아파트",
            84.5,
            "12",
        ),
        (
            "officetel",
            {"offiNm": "샘플오피스텔", "excluUseAr": "45.2", "floor": "7"},
            "샘플오피스텔",
            45.2,
            "7",
        ),
        (
            "row_house",
            {"mhouseNm": "샘플연립", "excluUseAr": "60.1", "floor": "3"},
            "샘플연립",
            60.1,
            "3",
        ),
        (
            "detached_house",
            {"totalFloorAr": "120.0"},
            "",
            120.0,
            "",
        ),
        (
            "commercial",
            {"buildingAr": "200.0", "floor": "2"},
            "",
            200.0,
            "2",
        ),
    ],
)
def test_molit_normalize_item_maps_fields_per_property_type(
    property_type: str,
    raw: dict,
    expected_name: str,
    expected_area: float,
    expected_floor: str,
) -> None:
    config = PROPERTY_TYPE_CONFIG[property_type]
    raw = {
        **raw,
        "umdNm": "역삼동",
        "jibun": "123-4",
        "dealAmount": "50,000",
        "dealYear": "2026",
        "dealMonth": "7",
        "dealDay": "1",
        "buildYear": "2015",
    }

    result = RealTransactionConnector._normalize_item(
        raw, property_type, config, sido="서울특별시", sigungu="강남구"
    )

    assert result["property_type"] == property_type
    assert result["complex_name"] == expected_name
    assert result["exclusive_area"] == expected_area
    assert result["floor_info"] == expected_floor
    assert result["deal_price"] == 500_000_000  # "50,000"만원 -> 원
