"""경매 물건 검색/상세 Pydantic v2 스키마 (지시서 §7.2, §7.3).

검색 API(§7.2)/상세 API(§7.3) 응답 필드 구성은 지시서 예시와 정확히 일치시킨다.
"""

from __future__ import annotations

from datetime import date, datetime

from pydantic import BaseModel

from app.schemas.common import ORMBase


class AuctionItemCreate(BaseModel):
    source: str
    source_item_id: str | None = None
    auction_type: str

    case_number: str | None = None
    item_number: str | None = None
    category: str | None = None
    sub_category: str | None = None

    title: str | None = None
    address: str | None = None
    sido: str | None = None
    sigungu: str | None = None
    eupmyeondong: str | None = None

    latitude: float | None = None
    longitude: float | None = None

    appraisal_price: int | None = None
    minimum_price: int | None = None
    deposit_price: int | None = None

    bid_date: datetime | None = None
    bid_location: str | None = None
    fail_count: int = 0

    status: str | None = "active"


class AuctionItemRead(ORMBase):
    id: int
    source: str
    source_item_id: str | None = None
    auction_type: str

    case_number: str | None = None
    item_number: str | None = None
    category: str | None = None
    sub_category: str | None = None

    title: str | None = None
    address: str | None = None
    sido: str | None = None
    sigungu: str | None = None
    eupmyeondong: str | None = None

    latitude: float | None = None
    longitude: float | None = None

    appraisal_price: int | None = None
    minimum_price: int | None = None
    deposit_price: int | None = None

    bid_date: datetime | None = None
    bid_location: str | None = None
    fail_count: int

    status: str | None = None

    view_count: int
    watch_count: int

    created_at: datetime
    updated_at: datetime


# ---------------------------------------------------------------------------
# 검색 API (지시서 §7.2)
# ---------------------------------------------------------------------------


class AuctionItemSearchItem(BaseModel):
    """검색 결과 리스트 항목 (지시서 §7.2 응답 예시)."""

    id: int
    source: str
    auction_type: str
    case_number: str | None = None
    item_number: str | None = None
    category: str | None = None
    title: str | None = None
    address: str | None = None
    sido: str | None = None
    sigungu: str | None = None
    appraisal_price: int | None = None
    minimum_price: int | None = None
    fail_count: int
    bid_date: datetime | None = None
    predicted_price_mid: int | None = None
    predicted_rate_mid: float | None = None
    risk_level: str | None = None
    verdict: str | None = None
    status: str | None = None
    view_count: int = 0
    watch_count: int = 0


class AuctionItemSearchPagination(BaseModel):
    page: int
    limit: int
    total: int
    total_pages: int


class AuctionItemSearchResponse(BaseModel):
    items: list[AuctionItemSearchItem]
    pagination: AuctionItemSearchPagination


# ---------------------------------------------------------------------------
# 상세 API (지시서 §7.3)
# ---------------------------------------------------------------------------


class RealEstateDetailRead(ORMBase):
    building_area: float | None = None
    land_area: float | None = None
    exclusive_area: float | None = None
    floor_info: str | None = None
    approval_date: date | None = None
    land_rights: str | None = None
    building_structure: str | None = None
    usage_type: str | None = None
    appraisal_summary: str | None = None
    occupancy_summary: str | None = None
    tenant_summary: str | None = None
    registry_summary: str | None = None
    document_summary: str | None = None


class VehicleDetailRead(ORMBase):
    manufacturer: str | None = None
    model: str | None = None
    trim: str | None = None
    model_year: int | None = None
    mileage: int | None = None
    fuel_type: str | None = None
    transmission: str | None = None
    color: str | None = None
    accident_history: str | None = None
    inspection_summary: str | None = None
    storage_location: str | None = None


class LatestPredictionRead(BaseModel):
    predicted_price_low: int | None = None
    predicted_price_mid: int | None = None
    predicted_price_high: int | None = None
    predicted_rate_low: float | None = None
    predicted_rate_mid: float | None = None
    predicted_rate_high: float | None = None
    confidence: str | None = None
    model_version: str | None = None
    verdict: str | None = None


class RiskAssessmentSummary(BaseModel):
    risk_level: str | None = None
    risk_factors: list[str] = []


class NearbyTransaction(BaseModel):
    complex_name: str | None = None
    address: str | None = None
    exclusive_area: float | None = None
    deal_price: int | None = None
    deal_year: int | None = None
    deal_month: int | None = None
    deal_day: int | None = None
    floor_info: str | None = None
    build_year: int | None = None


class AuctionItemDetailResponse(BaseModel):
    id: int
    source: str
    auction_type: str
    case_number: str | None = None
    item_number: str | None = None
    category: str | None = None
    title: str | None = None
    address: str | None = None
    appraisal_price: int | None = None
    minimum_price: int | None = None
    deposit_price: int | None = None
    fail_count: int
    bid_date: datetime | None = None
    view_count: int = 0
    watch_count: int = 0
    real_estate_detail: RealEstateDetailRead | None = None
    vehicle_detail: VehicleDetailRead | None = None
    latest_prediction: LatestPredictionRead | None = None
    risk_assessment: RiskAssessmentSummary | None = None
    nearby_transactions: list[NearbyTransaction] = []
    disclaimer: str
