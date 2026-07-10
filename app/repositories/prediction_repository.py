"""price_predictions / risk_assessments DB 접근 계층 (지시서 §6.7, §6.12, §8)."""

from __future__ import annotations

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.auction_item import AuctionItem
from app.models.auction_result import AuctionResult
from app.models.price_prediction import PricePrediction
from app.models.property_transaction import PropertyTransaction
from app.models.risk_assessment import RiskAssessment


class PredictionRepository:
    """PricePrediction / RiskAssessment 조회·저장, 예측 계산에 필요한 참조 데이터 조회."""

    def __init__(self, session: AsyncSession) -> None:
        self.session = session

    async def get_auction_item(self, auction_item_id: int) -> AuctionItem | None:
        return await self.session.get(AuctionItem, auction_item_id)

    async def get_similar_sold_results(
        self, category: str | None, exclude_auction_item_id: int
    ) -> list[tuple[AuctionResult, AuctionItem]]:
        """동일 카테고리의 낙찰(sold) 사례를 자기 자신을 제외하고 조회한다.

        각 낙찰 사례가 속한 auction_item(감정가/최저가 참조용)도 함께 반환한다.
        """
        if not category:
            return []
        stmt = (
            select(AuctionResult, AuctionItem)
            .join(AuctionItem, AuctionResult.auction_item_id == AuctionItem.id)
            .where(
                AuctionItem.category == category,
                AuctionItem.id != exclude_auction_item_id,
                AuctionResult.result_status == "sold",
                AuctionResult.winning_price.is_not(None),
            )
        )
        result = await self.session.execute(stmt)
        return list(result.all())

    async def get_nearby_transactions(
        self, sido: str | None, sigungu: str | None
    ) -> list[PropertyTransaction]:
        """동일 시/도 + 시군구 기준 인근 실거래가 조회 (§8.7 시세괴리 계산용)."""
        if not sido or not sigungu:
            return []
        stmt = select(PropertyTransaction).where(
            PropertyTransaction.sido == sido,
            PropertyTransaction.sigungu == sigungu,
        )
        result = await self.session.execute(stmt)
        return list(result.scalars().all())

    async def get_latest_risk_assessment(self, auction_item_id: int) -> RiskAssessment | None:
        stmt = (
            select(RiskAssessment)
            .where(RiskAssessment.auction_item_id == auction_item_id)
            .order_by(RiskAssessment.created_at.desc())
            .limit(1)
        )
        return await self.session.scalar(stmt)

    async def get_latest_prediction(self, auction_item_id: int) -> PricePrediction | None:
        stmt = (
            select(PricePrediction)
            .where(PricePrediction.auction_item_id == auction_item_id)
            .order_by(PricePrediction.created_at.desc())
            .limit(1)
        )
        return await self.session.scalar(stmt)

    async def save_prediction(self, prediction: PricePrediction) -> PricePrediction:
        self.session.add(prediction)
        await self.session.commit()
        await self.session.refresh(prediction)
        return prediction

    async def save_risk_assessment(self, risk_assessment: RiskAssessment) -> RiskAssessment:
        self.session.add(risk_assessment)
        await self.session.commit()
        await self.session.refresh(risk_assessment)
        return risk_assessment
