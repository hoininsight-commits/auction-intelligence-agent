"""권리 위험 체크리스트 서비스 (지시서 §6.12, §7.3 risk_assessment 필드 대응).

MVP 기본 서비스 수준: risk_assessments 테이블에 저장된 최신 평가를 조회하고,
평가가 없는 물건에 대해서는 물건 정보(유찰 횟수, 상세 정보 존재 여부)만으로
간단한 기본 위험도를 생성한다. 실제 등기부/권리분석 엔진은 범위 밖이다.
"""
from __future__ import annotations

from app.core.disclaimers import RISK_ANALYSIS_DISCLAIMER
from app.models.auction_item import AuctionItem
from app.models.risk_assessment import RiskAssessment
from app.repositories.prediction_repository import PredictionRepository


class RiskAnalysisService:
    def __init__(self, repository: PredictionRepository) -> None:
        self.repository = repository

    async def get_latest_or_default(self, auction_item: AuctionItem) -> RiskAssessment:
        """최신 위험도 평가를 조회하고, 없으면 저장하지 않는 기본값을 즉석 생성해 반환한다."""
        existing = await self.repository.get_latest_risk_assessment(auction_item.id)
        if existing is not None:
            return existing
        return self._build_default_assessment(auction_item)

    def _build_default_assessment(self, auction_item: AuctionItem) -> RiskAssessment:
        """유찰 횟수 등 단순 신호만으로 산출하는 기본(참고용) 위험도.

        DB에 저장하지 않는 비영속 인스턴스를 반환한다 (필요 시 호출부에서 저장).
        """
        fail_count = auction_item.fail_count or 0

        if fail_count >= 3:
            risk_level = "high"
            legal_score, occupancy_score, asset_score = 70.0, 55.0, 50.0
        elif fail_count >= 1:
            risk_level = "medium"
            legal_score, occupancy_score, asset_score = 45.0, 30.0, 30.0
        else:
            risk_level = "unknown"
            legal_score, occupancy_score, asset_score = 40.0, 25.0, 25.0

        factors: list[str] = ["점유자 확인 필요", "매각물건명세서 확인 필요"]
        if fail_count >= 2:
            factors.append(f"유찰 {fail_count}회 물건으로 권리관계 재확인 필요")

        return RiskAssessment(
            auction_item_id=auction_item.id,
            risk_level=risk_level,
            legal_risk_score=legal_score,
            occupancy_risk_score=occupancy_score,
            asset_risk_score=asset_score,
            risk_factors={"factors": factors},
            disclaimer=RISK_ANALYSIS_DISCLAIMER,
        )
