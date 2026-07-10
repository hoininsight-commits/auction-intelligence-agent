"""수익률 계산 API 테스트 (지시서 §13.5, §7.7).

계산 공식은 app/services/profitability_service.py에 구현된 지시서 §7.7 "계산 기준" 그대로다:
  total_cost = 취득세 + 법무비 + 명도비 + 수리비 + 중개수수료
  interest_cost = loan_amount * annual_interest_rate / 100 * holding_months / 12
  total_investment = (purchase_price - loan_amount) + total_cost
  net_profit = expected_sale_price - purchase_price - total_cost - interest_cost + expected_rental_income
  roi = net_profit / total_investment * 100
  break_even_sale_price = purchase_price + total_cost + interest_cost - expected_rental_income
  safety_margin = expected_sale_price - break_even_sale_price

주의: 원본 개발지시서 §7.7의 응답 "예시" 값(safety_margin: 42,000,000)은 지시서 자체의
공식으로 재계산하면 맞지 않는다(공식대로면 7,750,000이 나와야 함). 실제 구현은 예시가 아니라
공식을 따르고 있으며, 아래 테스트도 공식 기준으로 직접 계산한 기대값을 사용한다.
"""
from __future__ import annotations

from httpx import AsyncClient

PAYLOAD = {
    "purchase_price": 800_000_000,
    "expected_sale_price": 900_000_000,
    "acquisition_tax": 20_000_000,
    "legal_fee": 2_000_000,
    "eviction_cost": 5_000_000,
    "repair_cost": 10_000_000,
    "brokerage_fee": 3_000_000,
    "loan_amount": 400_000_000,
    "annual_interest_rate": 4.0,
    "holding_months": 12,
    "monthly_rent": 0,
}


async def test_profitability_roi_calculation_accuracy(client: AsyncClient) -> None:
    response = await client.post("/api/v1/profitability/calculate", json=PAYLOAD)

    assert response.status_code == 200
    body = response.json()

    total_cost = 20_000_000 + 2_000_000 + 5_000_000 + 10_000_000 + 3_000_000  # 40,000,000
    interest_cost = 400_000_000 * 4.0 / 100 * 12 / 12  # 16,000,000
    total_investment = (800_000_000 - 400_000_000) + total_cost  # 440,000,000
    net_profit = 900_000_000 - 800_000_000 - total_cost - interest_cost + 0  # 44,000,000
    expected_roi = round(net_profit / total_investment * 100, 2)  # 10.0
    expected_annualized_roi = round(expected_roi * 12 / 12, 2)  # 10.0

    assert body["total_cost"] == total_cost
    assert body["total_investment"] == total_investment
    assert body["interest_cost"] == interest_cost
    assert body["net_profit"] == net_profit
    assert body["roi"] == expected_roi
    assert body["annualized_roi"] == expected_annualized_roi
    assert body["disclaimer"]


async def test_profitability_break_even_sale_price(client: AsyncClient) -> None:
    response = await client.post("/api/v1/profitability/calculate", json=PAYLOAD)

    assert response.status_code == 200
    body = response.json()

    total_cost = 40_000_000
    interest_cost = 16_000_000
    expected_break_even = 800_000_000 + total_cost + interest_cost - 0  # 856,000,000
    expected_safety_margin = 900_000_000 - expected_break_even  # 44,000,000

    assert body["break_even_sale_price"] == expected_break_even
    assert body["safety_margin"] == expected_safety_margin


async def test_profitability_holding_months_zero_is_validation_error(client: AsyncClient) -> None:
    payload = {**PAYLOAD, "holding_months": 0}

    response = await client.post("/api/v1/profitability/calculate", json=payload)

    assert response.status_code == 422


async def test_profitability_holding_months_negative_is_validation_error(client: AsyncClient) -> None:
    payload = {**PAYLOAD, "holding_months": -3}

    response = await client.post("/api/v1/profitability/calculate", json=payload)

    assert response.status_code == 422
