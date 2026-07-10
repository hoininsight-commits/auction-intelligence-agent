"""데이터 품질 검증 서비스 (지시서 §10, §7.8).

검증 항목 (지시서 §10 그대로):
  1. 감정가가 null 또는 0인지 확인
  2. 최저가가 null 또는 0인지 확인
  3. 최저가가 감정가보다 비정상적으로 높은지 확인
  4. 입찰일이 과거인데 상태가 active인지 확인
  5. 주소가 비어 있는지 확인
  6. 좌표가 없는지 확인
  7. 중복 사건번호가 있는지 확인
  8. 예상 낙찰가가 없는 active 물건 수 확인
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timezone

from sqlalchemy import distinct, func, or_, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.auction_item import AuctionItem
from app.models.price_prediction import PricePrediction


@dataclass
class DataQualitySummary:
    total_items: int
    missing_appraisal_price: int
    missing_minimum_price: int
    invalid_minimum_price_over_appraisal: int
    past_bid_date_active_status: int
    missing_address: int
    missing_coordinates: int
    duplicate_case_numbers: int
    prediction_missing: int


class DataQualityService:
    def __init__(self, session: AsyncSession) -> None:
        self.session = session

    async def get_summary(self) -> DataQualitySummary:
        total_items = await self.session.scalar(select(func.count(AuctionItem.id))) or 0

        # 1. 감정가 null 또는 0
        missing_appraisal_price = await self._count(
            or_(AuctionItem.appraisal_price.is_(None), AuctionItem.appraisal_price == 0)
        )

        # 2. 최저가 null 또는 0
        missing_minimum_price = await self._count(
            or_(AuctionItem.minimum_price.is_(None), AuctionItem.minimum_price == 0)
        )

        # 3. 최저가가 감정가보다 비정상적으로 높은지
        invalid_minimum_price_over_appraisal = await self._count(
            AuctionItem.minimum_price.is_not(None),
            AuctionItem.appraisal_price.is_not(None),
            AuctionItem.minimum_price > AuctionItem.appraisal_price,
        )

        # 4. 입찰일이 과거인데 상태가 active인지
        now = datetime.now(timezone.utc).replace(tzinfo=None)
        past_bid_date_active_status = await self._count(
            AuctionItem.bid_date.is_not(None),
            AuctionItem.bid_date < now,
            AuctionItem.status == "active",
        )

        # 5. 주소가 비어 있는지
        missing_address = await self._count(
            or_(AuctionItem.address.is_(None), func.trim(AuctionItem.address) == "")
        )

        # 6. 좌표가 없는지
        missing_coordinates = await self._count(
            or_(AuctionItem.latitude.is_(None), AuctionItem.longitude.is_(None))
        )

        # 7. 중복 사건번호가 있는지 (사건번호 그룹 중 2건 이상 존재하는 그룹 수)
        duplicate_case_numbers = await self._count_duplicate_case_numbers()

        # 8. 예상 낙찰가가 없는 active 물건 수
        prediction_missing = await self._count_prediction_missing_active()

        return DataQualitySummary(
            total_items=total_items,
            missing_appraisal_price=missing_appraisal_price,
            missing_minimum_price=missing_minimum_price,
            invalid_minimum_price_over_appraisal=invalid_minimum_price_over_appraisal,
            past_bid_date_active_status=past_bid_date_active_status,
            missing_address=missing_address,
            missing_coordinates=missing_coordinates,
            duplicate_case_numbers=duplicate_case_numbers,
            prediction_missing=prediction_missing,
        )

    async def _count(self, *conditions) -> int:
        stmt = select(func.count(AuctionItem.id)).where(*conditions)
        return await self.session.scalar(stmt) or 0

    async def _count_duplicate_case_numbers(self) -> int:
        subq = (
            select(AuctionItem.case_number)
            .where(AuctionItem.case_number.is_not(None))
            .group_by(AuctionItem.case_number)
            .having(func.count(AuctionItem.id) > 1)
        )
        result = await self.session.execute(select(func.count()).select_from(subq.subquery()))
        return result.scalar() or 0

    async def _count_prediction_missing_active(self) -> int:
        subq = select(distinct(PricePrediction.auction_item_id)).where(
            PricePrediction.auction_item_id.is_not(None)
        )
        stmt = select(func.count(AuctionItem.id)).where(
            AuctionItem.status == "active",
            AuctionItem.id.not_in(subq),
        )
        return await self.session.scalar(stmt) or 0
