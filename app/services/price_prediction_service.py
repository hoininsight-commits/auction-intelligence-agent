"""룰 기반 참고 낙찰가 서비스 (지시서 §8, rule-v1).

우선순위 (§8.2):
  1. 유사 낙찰 사례 평균 낙찰가율 × 감정가
  2. (유사 사례 부족 시) 최저가 대비 평균 낙찰 배수 × 최저가
  3. (그마저 부족 시) 카테고리별 기본 낙찰가율 × 감정가

보정계수 (§8.8) = 유찰횟수계수 × 권리위험계수 × 지역수요계수 × 시세괴리계수는
어느 기본 공식을 사용했든 마지막 단계에서 동일하게 적용한다 ("최종 보정계수").

신뢰도(§8.10)는 원 지시서 기준(유사사례 30건 이상 등)이 MVP mock 데이터로는
사실상 항상 "낮음"만 나오므로, 실제로 high/medium/low가 골고루 나오도록
기준을 완화해서 사용한다 (아래 _determine_confidence 참고).
"""

from __future__ import annotations

from dataclasses import dataclass, field

from app.core.constants import (
    DEFAULT_WINNING_RATE_BY_CATEGORY,
    FAIL_COUNT_COEFFICIENT,
    FAIL_COUNT_COEFFICIENT_5_PLUS,
    PREDICTION_RANGE_NARROW,
    PREDICTION_RANGE_WIDE,
    PRICE_GAP_COEFFICIENT_ABOVE_MAX,
    PRICE_GAP_COEFFICIENT_BANDS,
    PRICE_GAP_COEFFICIENT_NO_DATA,
    REGION_DEMAND_COEFFICIENT,
    RISK_COEFFICIENT,
    RULE_PREDICTION_MODEL_NAME,
    VERDICT_CAUTION_PRICE_GAP_MIN,
    VERDICT_GOOD_PRICE_GAP_MAX,
)
from app.core.disclaimers import PREDICTION_DISCLAIMER
from app.models.auction_item import AuctionItem
from app.models.price_prediction import PricePrediction
from app.repositories.prediction_repository import PredictionRepository
from app.services.risk_analysis_service import RiskAnalysisService

# MVP 완화 기준: 유사 낙찰 사례가 이 값 이상이면 "유사 사례 평균 낙찰가율" 방식(§8.2 1번)을 사용한다.
# 원 지시서(§8.10)의 "30건 이상"은 mock seed 데이터 규모상 도달 불가능하므로 완화했다.
SIMILAR_CASE_METHOD_MIN_COUNT = 4

# 신뢰도 판정 완화 기준 (§8.10, MVP)
CONFIDENCE_HIGH_MIN_SIMILAR = 4
CONFIDENCE_HIGH_MIN_TRANSACTIONS = 3
CONFIDENCE_MEDIUM_MIN_SIMILAR = 1
CONFIDENCE_MEDIUM_MIN_TRANSACTIONS = 1


@dataclass
class PredictionCalculation:
    auction_item_id: int
    predicted_price_low: int
    predicted_price_mid: int
    predicted_price_high: int
    predicted_rate_low: float | None
    predicted_rate_mid: float | None
    predicted_rate_high: float | None
    confidence: str
    model_version: str
    explanation: list[str] = field(default_factory=list)
    disclaimer: str = PREDICTION_DISCLAIMER
    base_method: str = ""
    adjustment_factor: float = 1.0
    verdict: str = "fair"


class PricePredictionService:
    def __init__(self, repository: PredictionRepository) -> None:
        self.repository = repository
        self.risk_service = RiskAnalysisService(repository)

    async def predict_price(self, auction_item_id: int) -> PredictionCalculation | None:
        auction_item = await self.repository.get_auction_item(auction_item_id)
        if auction_item is None:
            return None

        similar_pairs = await self.repository.get_similar_sold_results(
            auction_item.category, exclude_auction_item_id=auction_item_id
        )
        transactions = await self.repository.get_nearby_transactions(
            auction_item.sido, auction_item.sigungu
        )
        risk_assessment = await self.risk_service.get_latest_or_default(auction_item)

        explanation: list[str] = []

        # ------------------------------------------------------------------
        # §8.2 기본 공식: 유사 사례 -> 최저가 배수 -> 카테고리 기본 낙찰가율
        # ------------------------------------------------------------------
        base_price, base_method = self._compute_base_price(auction_item, similar_pairs, explanation)

        # ------------------------------------------------------------------
        # §8.4~§8.8 보정계수
        # ------------------------------------------------------------------
        fail_count = auction_item.fail_count or 0
        fail_coefficient = FAIL_COUNT_COEFFICIENT.get(fail_count, FAIL_COUNT_COEFFICIENT_5_PLUS)
        explanation.append(
            f"유찰 {fail_count}회 물건의 보정계수({fail_coefficient})를 적용했습니다."
        )

        risk_level = risk_assessment.risk_level or "unknown"
        risk_coefficient = RISK_COEFFICIENT.get(risk_level, RISK_COEFFICIENT["unknown"])
        if risk_level == "unknown":
            explanation.append("권리 위험도 정보가 부족하여 보수적 범위를 적용했습니다.")
        else:
            explanation.append(
                f"권리 위험도({risk_level})에 따른 보정계수({risk_coefficient})를 적용했습니다."
            )

        region_coefficient = REGION_DEMAND_COEFFICIENT.get(
            auction_item.sido or "", REGION_DEMAND_COEFFICIENT["default"]
        )
        explanation.append(
            f"지역({auction_item.sido or '기타'}) 수요 보정계수({region_coefficient})를 적용했습니다."
        )

        price_gap_coefficient, price_gap_ratio = self._compute_price_gap_coefficient(
            auction_item, transactions, explanation
        )

        adjustment_factor = (
            fail_coefficient * risk_coefficient * region_coefficient * price_gap_coefficient
        )

        verdict = self._determine_verdict(price_gap_ratio, risk_level)
        explanation.append(f"종합판정: {verdict}")

        median_price = base_price * adjustment_factor

        # ------------------------------------------------------------------
        # §8.10 신뢰도 (MVP 완화 기준)
        # ------------------------------------------------------------------
        confidence = self._determine_confidence(len(similar_pairs), len(transactions))
        explanation.append(
            f"유사 낙찰 사례 {len(similar_pairs)}건, 인근 실거래가 {len(transactions)}건을 근거로 신뢰도를 '{confidence}'로 산정했습니다."
        )

        # ------------------------------------------------------------------
        # §8.9 예측 범위
        # ------------------------------------------------------------------
        low_ratio, high_ratio = (
            PREDICTION_RANGE_WIDE if confidence == "low" else PREDICTION_RANGE_NARROW
        )
        price_low = round(median_price * low_ratio)
        price_mid = round(median_price)
        price_high = round(median_price * high_ratio)

        appraisal_price = auction_item.appraisal_price
        rate_low, rate_mid, rate_high = self._compute_rates(
            appraisal_price, price_low, price_mid, price_high
        )

        return PredictionCalculation(
            auction_item_id=auction_item_id,
            predicted_price_low=price_low,
            predicted_price_mid=price_mid,
            predicted_price_high=price_high,
            predicted_rate_low=rate_low,
            predicted_rate_mid=rate_mid,
            predicted_rate_high=rate_high,
            confidence=confidence,
            model_version=RULE_PREDICTION_MODEL_NAME,
            explanation=explanation,
            disclaimer=PREDICTION_DISCLAIMER,
            base_method=base_method,
            adjustment_factor=adjustment_factor,
            verdict=verdict,
        )

    async def predict_and_save(self, auction_item_id: int) -> PredictionCalculation | None:
        calculation = await self.predict_price(auction_item_id)
        if calculation is None:
            return None

        prediction = PricePrediction(
            auction_item_id=calculation.auction_item_id,
            predicted_price_low=calculation.predicted_price_low,
            predicted_price_mid=calculation.predicted_price_mid,
            predicted_price_high=calculation.predicted_price_high,
            predicted_rate_low=calculation.predicted_rate_low,
            predicted_rate_mid=calculation.predicted_rate_mid,
            predicted_rate_high=calculation.predicted_rate_high,
            confidence=calculation.confidence,
            model_version=calculation.model_version,
            explanation={
                "messages": calculation.explanation,
                "base_method": calculation.base_method,
                "adjustment_factor": round(calculation.adjustment_factor, 6),
                "verdict": calculation.verdict,
            },
            disclaimer=calculation.disclaimer,
        )
        await self.repository.save_prediction(prediction)
        calculation.auction_item_id = prediction.auction_item_id
        return calculation

    # ------------------------------------------------------------------
    # 내부 계산 helper
    # ------------------------------------------------------------------

    def _compute_base_price(
        self,
        auction_item: AuctionItem,
        similar_pairs: list[tuple],
        explanation: list[str],
    ) -> tuple[float, str]:
        appraisal_price = auction_item.appraisal_price or 0
        minimum_price = auction_item.minimum_price or 0

        # 1) 유사 낙찰 사례 평균 낙찰가율 (§8.2 공식 1)
        if len(similar_pairs) >= SIMILAR_CASE_METHOD_MIN_COUNT and appraisal_price > 0:
            rates = [
                result.winning_price / ref_item.appraisal_price
                for result, ref_item in similar_pairs
                if result.winning_price and ref_item.appraisal_price
            ]
            if rates:
                avg_rate = sum(rates) / len(rates)
                explanation.append(
                    f"유사 물건 {len(rates)}건의 평균 낙찰가율({avg_rate * 100:.1f}%)을 기준으로 계산했습니다."
                )
                return appraisal_price * avg_rate, "similar_case_average"

        # 2) 최저가 대비 평균 낙찰 배수 (§8.2 공식 2, fallback)
        if similar_pairs and minimum_price > 0:
            multiples = [
                result.winning_price / ref_item.minimum_price
                for result, ref_item in similar_pairs
                if result.winning_price and ref_item.minimum_price
            ]
            if multiples:
                avg_multiple = sum(multiples) / len(multiples)
                explanation.append(
                    f"유사 낙찰 사례가 부족하여 최저가 대비 평균 낙찰 배수({avg_multiple:.3f})를 기준으로 계산했습니다."
                )
                return minimum_price * avg_multiple, "minimum_price_multiple"

        # 3) 카테고리별 기본 낙찰가율 (§8.2 공식 3, 최종 fallback)
        if appraisal_price > 0:
            default_rate = DEFAULT_WINNING_RATE_BY_CATEGORY.get(auction_item.category or "", None)
            if default_rate is None:
                # 카테고리 매칭이 안 되는 경우를 위한 안전한 기본값 (지시서 표에 없는 카테고리 대비)
                default_rate = sum(DEFAULT_WINNING_RATE_BY_CATEGORY.values()) / len(
                    DEFAULT_WINNING_RATE_BY_CATEGORY
                )
            explanation.append(
                f"유사 낙찰 사례와 최저가 정보가 모두 부족하여 카테고리 기본 낙찰가율({default_rate * 100:.0f}%)을 기준으로 계산했습니다."
            )
            return appraisal_price * default_rate, "default_category_rate"

        # 극단적 fallback: 감정가도 없는 경우 최저가라도 사용
        explanation.append("감정가 정보가 없어 최저가를 기준으로 계산했습니다.")
        return float(minimum_price), "minimum_price_only"

    def _compute_price_gap_coefficient(
        self,
        auction_item: AuctionItem,
        transactions: list,
        explanation: list[str],
    ) -> tuple[float, float | None]:
        appraisal_price = auction_item.appraisal_price
        deal_prices = [t.deal_price for t in transactions if t.deal_price]
        if not appraisal_price or not deal_prices:
            explanation.append(
                "인근 실거래가 데이터가 없어 시세괴리 보정계수는 적용하지 않았습니다(1.00)."
            )
            return PRICE_GAP_COEFFICIENT_NO_DATA, None

        avg_deal_price = sum(deal_prices) / len(deal_prices)
        if avg_deal_price <= 0:
            return PRICE_GAP_COEFFICIENT_NO_DATA, None

        price_gap_ratio = appraisal_price / avg_deal_price
        for upper_bound, coefficient in PRICE_GAP_COEFFICIENT_BANDS:
            if price_gap_ratio <= upper_bound:
                explanation.append(
                    f"인근 실거래가 평균 대비 시세괴리율({price_gap_ratio:.2f})에 따른 보정계수({coefficient})를 적용했습니다."
                )
                return coefficient, price_gap_ratio

        explanation.append(
            f"인근 실거래가 평균 대비 시세괴리율({price_gap_ratio:.2f})이 커서 보정계수({PRICE_GAP_COEFFICIENT_ABOVE_MAX})를 적용했습니다."
        )
        return PRICE_GAP_COEFFICIENT_ABOVE_MAX, price_gap_ratio

    def _determine_verdict(self, price_gap_ratio: float | None, risk_level: str) -> str:
        """예상낙찰가율이 아니라 시세괴리율(§8.7)과 위험도(§8.5)만으로 판정한다.

        예측 범위(low/mid/high)는 시세괴리 보정계수가 이미 반영된 결과라 그걸 다시
        verdict 기준으로 쓰면 순환 참조가 된다. 그래서 verdict는 보정 전 원재료인
        시세괴리율/위험도만 독립적으로 본다.
        """
        if risk_level == "high":
            return "caution"
        if price_gap_ratio is not None and price_gap_ratio > VERDICT_CAUTION_PRICE_GAP_MIN:
            return "caution"
        if (
            price_gap_ratio is not None
            and price_gap_ratio <= VERDICT_GOOD_PRICE_GAP_MAX
            and risk_level == "low"
        ):
            return "good"
        return "fair"

    def _determine_confidence(self, similar_count: int, transaction_count: int) -> str:
        """§8.10 신뢰도 산정 기준의 MVP 완화 버전.

        원 지시서는 "유사 낙찰 사례 30건 이상=높음" 등 실거래 규모의 실제 서비스를
        전제로 하므로, mock seed 데이터(물건 몇 건, 유사 사례 0~5건 수준)에서는
        항상 "낮음"만 나오게 된다. MVP에서는 실제로 세 등급이 모두 관측되도록
        아래처럼 완화된 기준을 사용한다.
        """
        if (
            similar_count >= CONFIDENCE_HIGH_MIN_SIMILAR
            and transaction_count >= CONFIDENCE_HIGH_MIN_TRANSACTIONS
        ):
            return "high"
        if (
            similar_count >= CONFIDENCE_MEDIUM_MIN_SIMILAR
            or transaction_count >= CONFIDENCE_MEDIUM_MIN_TRANSACTIONS
        ):
            return "medium"
        return "low"

    def _compute_rates(
        self,
        appraisal_price: int | None,
        price_low: int,
        price_mid: int,
        price_high: int,
    ) -> tuple[float | None, float | None, float | None]:
        if not appraisal_price:
            return None, None, None
        return (
            round(price_low / appraisal_price * 100, 2),
            round(price_mid / appraisal_price * 100, 2),
            round(price_high / appraisal_price * 100, 2),
        )
