"""raw_source_records -> auction_items / property_transactions 정규화 서비스 (지시서 §9.1, §9.5).

Connector가 반환한 원본 dict(§9.3, §9.4 필드 형태)를 정규화된 테이블 컬럼에 맞춰 변환하고,
`source_item_id` 기준으로 upsert 한다. `property_transactions`는 개별 식별자가 없는
이력성 데이터이므로 (sido/sigungu/complex_name/exclusive_area/deal_price/deal_year/
deal_month/deal_day) 조합으로 중복 여부를 판단해 upsert 한다.
"""
from __future__ import annotations

from datetime import datetime
from typing import Any

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.auction_item import AuctionItem
from app.models.property_transaction import PropertyTransaction
from app.services.geocoding_service import GeocodingService, geocoding_service

# auction_items 테이블 컬럼 중 원본 dict에서 그대로/거의 그대로 옮길 수 있는 필드
_AUCTION_ITEM_FIELDS = (
    "source",
    "source_item_id",
    "auction_type",
    "case_number",
    "item_number",
    "category",
    "sub_category",
    "title",
    "address",
    "sido",
    "sigungu",
    "eupmyeondong",
    "appraisal_price",
    "minimum_price",
    "deposit_price",
    "bid_location",
    "fail_count",
    "status",
)

_PROPERTY_TRANSACTION_FIELDS = (
    "property_type",
    "address",
    "sido",
    "sigungu",
    "eupmyeondong",
    "complex_name",
    "exclusive_area",
    "deal_price",
    "deal_year",
    "deal_month",
    "deal_day",
    "floor_info",
    "build_year",
    "source",
)


def _parse_datetime(value: Any) -> datetime | None:
    if value is None:
        return None
    if isinstance(value, datetime):
        return value
    if isinstance(value, str):
        try:
            return datetime.fromisoformat(value)
        except ValueError:
            return None
    return None


class NormalizationService:
    """Connector 원본 데이터를 정규화 테이블에 반영하는 서비스."""

    def __init__(self, session: AsyncSession, geocoder: GeocodingService | None = None) -> None:
        self.session = session
        self.geocoder = geocoder or geocoding_service

    # -- auction_items (온비드/경매 등) ---------------------------------------

    def normalize_auction_item(
        self, raw: dict[str, Any], *, raw_source_record_id: int | None = None
    ) -> dict[str, Any]:
        """원본 dict를 auction_items 컬럼 형태의 dict로 정규화한다."""
        normalized: dict[str, Any] = {
            field: raw.get(field) for field in _AUCTION_ITEM_FIELDS
        }
        normalized["bid_date"] = _parse_datetime(raw.get("bid_date"))
        normalized["fail_count"] = normalized.get("fail_count") or 0
        normalized["status"] = normalized.get("status") or "unknown"
        normalized["raw_source_record_id"] = raw_source_record_id
        return normalized

    async def upsert_auction_item(
        self, raw: dict[str, Any], *, raw_source_record_id: int | None = None
    ) -> tuple[AuctionItem, bool]:
        """source + source_item_id 기준으로 auction_items에 upsert 한다.

        Returns:
            (AuctionItem, created) — created=True면 새로 삽입, False면 기존 행 업데이트.
        """
        normalized = self.normalize_auction_item(raw, raw_source_record_id=raw_source_record_id)
        source = normalized["source"]
        source_item_id = normalized["source_item_id"]

        existing: AuctionItem | None = None
        if source and source_item_id:
            stmt = select(AuctionItem).where(
                AuctionItem.source == source,
                AuctionItem.source_item_id == source_item_id,
            )
            result = await self.session.execute(stmt)
            existing = result.scalar_one_or_none()

        # 좌표 확보 (지시서 §6.1 데이터 흐름 원칙 5 - 좌표는 항상 확보 시도)
        address = normalized.get("address")
        geocode = await self.geocoder.geocode(address)
        normalized["latitude"] = geocode.latitude
        normalized["longitude"] = geocode.longitude

        if existing is not None:
            for key, value in normalized.items():
                setattr(existing, key, value)
            await self.session.flush()
            return existing, False

        item = AuctionItem(**normalized)
        self.session.add(item)
        await self.session.flush()
        return item, True

    # -- property_transactions (실거래가) -------------------------------------

    def normalize_property_transaction(self, raw: dict[str, Any]) -> dict[str, Any]:
        """원본 dict를 property_transactions 컬럼 형태의 dict로 정규화한다."""
        return {field: raw.get(field) for field in _PROPERTY_TRANSACTION_FIELDS}

    async def upsert_property_transaction(
        self, raw: dict[str, Any]
    ) -> tuple[PropertyTransaction, bool]:
        """동일 거래(주소+면적+거래가+거래일) 조합이 이미 있으면 갱신, 없으면 삽입한다.

        property_transactions는 별도 source_item_id가 없는 이력성 데이터이므로
        자연키(주소/면적/거래가/거래연월일) 조합으로 중복을 판단한다.
        """
        normalized = self.normalize_property_transaction(raw)

        stmt = select(PropertyTransaction).where(
            PropertyTransaction.address == normalized.get("address"),
            PropertyTransaction.exclusive_area == normalized.get("exclusive_area"),
            PropertyTransaction.deal_price == normalized.get("deal_price"),
            PropertyTransaction.deal_year == normalized.get("deal_year"),
            PropertyTransaction.deal_month == normalized.get("deal_month"),
            PropertyTransaction.deal_day == normalized.get("deal_day"),
        )
        result = await self.session.execute(stmt)
        existing = result.scalar_one_or_none()

        if existing is not None:
            for key, value in normalized.items():
                setattr(existing, key, value)
            await self.session.flush()
            return existing, False

        transaction = PropertyTransaction(**normalized)
        self.session.add(transaction)
        await self.session.flush()
        return transaction, True
