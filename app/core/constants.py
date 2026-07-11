"""공통 상수 정의.

Phase 1: 최소한의 API 메타 상수만 정의. 룰 기반 예측 계수 등 도메인 상수는
Phase 4(가격 예측 서비스, 지시서 §8)에서 추가한다.
"""

API_V1_PREFIX = "/api/v1"

SERVICE_NAME = "Auction Intelligence Agent"

TEST_USER_ID = 1
TEST_USER_EMAIL = "test@example.com"
TEST_USER_NICKNAME = "테스트사용자"

RULE_PREDICTION_MODEL_NAME = "rule-v1"

# ---------------------------------------------------------------------------
# 룰 기반 참고 낙찰가 모델 (rule-v1, 지시서 §8) 계수 테이블
# 아래 값들은 지시서 §8.3~§8.7 그대로 옮긴 것이며 임의로 변경하지 않는다.
# ---------------------------------------------------------------------------

# §8.3 카테고리별 기본 낙찰가율 (감정가 기반, 유사 사례/최저가 배수 fallback마저 없을 때 사용)
DEFAULT_WINNING_RATE_BY_CATEGORY = {
    "apartment": 0.84,
    "villa": 0.78,
    "officetel": 0.80,
    "commercial": 0.72,
    "land": 0.70,
    "factory": 0.68,
    "vehicle": 0.75,
}

# §8.4 유찰 횟수 보정계수 (5회 이상은 0.85 고정)
FAIL_COUNT_COEFFICIENT = {
    0: 1.03,
    1: 1.00,
    2: 0.96,
    3: 0.92,
    4: 0.88,
}
FAIL_COUNT_COEFFICIENT_5_PLUS = 0.85

# §8.5 권리 위험 보정계수
RISK_COEFFICIENT = {
    "low": 1.00,
    "medium": 0.96,
    "high": 0.90,
    "unknown": 0.94,
}

# §8.6 지역 수요 보정계수
REGION_DEMAND_COEFFICIENT = {
    "서울특별시": 1.03,
    "경기도": 1.01,
    "인천광역시": 1.00,
    "부산광역시": 1.00,
    "대구광역시": 0.99,
    "대전광역시": 1.00,
    "광주광역시": 0.99,
    "울산광역시": 0.98,
    "세종특별자치시": 1.00,
    "default": 0.98,
}

# §8.7 시세 괴리 보정계수: (상한, 계수) 구간을 순서대로 검사한다.
# 시세괴리율 = 감정가 / 인근 실거래가 평균
#   <= 0.90            -> 1.03
#   0.90 < x <= 1.05    -> 1.00
#   1.05 < x <= 1.20    -> 0.97
#   1.20 <  x           -> 0.93
PRICE_GAP_COEFFICIENT_BANDS = [
    (0.90, 1.03),
    (1.05, 1.00),
    (1.20, 0.97),
]
PRICE_GAP_COEFFICIENT_ABOVE_MAX = 0.93
PRICE_GAP_COEFFICIENT_NO_DATA = 1.00

# 종합판정(verdict) 배지 기준 — 새 계산식을 만들지 않고 위 시세괴리 구간을 그대로 재사용한다.
# 시세괴리율 <= 0.90 (감정가가 시세보다 쌈) 이고 위험도 낮음 -> "good"
# 시세괴리율 > 1.20 (감정가가 시세보다 비쌈) 이거나 위험도 높음 -> "caution"
# 그 외 -> "fair"
VERDICT_GOOD_PRICE_GAP_MAX = PRICE_GAP_COEFFICIENT_BANDS[0][0]
VERDICT_CAUTION_PRICE_GAP_MIN = PRICE_GAP_COEFFICIENT_BANDS[-1][0]

# §8.9 예측 범위
PREDICTION_RANGE_NARROW = (0.97, 1.03)
PREDICTION_RANGE_WIDE = (0.94, 1.06)

# ---------------------------------------------------------------------------
# 검색 API (§7.2) max_risk_level 필터용 위험도 순서
# ---------------------------------------------------------------------------
RISK_LEVEL_ORDER = {
    "low": 1,
    "medium": 2,
    "high": 3,
}
