"""수익률 계산 Pydantic v2 스키마 (지시서 §7.7).

요청/응답 필드명 및 계산식은 지시서 §7.7 예시와 정확히 일치시킨다.
"""
from __future__ import annotations

from pydantic import BaseModel, Field


class ProfitabilityCalculateRequest(BaseModel):
    purchase_price: int
    expected_sale_price: int

    acquisition_tax: int = 0
    legal_fee: int = 0
    eviction_cost: int = 0
    repair_cost: int = 0
    brokerage_fee: int = 0

    loan_amount: int = 0
    annual_interest_rate: float = 0

    holding_months: int = Field(gt=0)

    monthly_rent: int = 0


class ProfitabilityCalculateResponse(BaseModel):
    purchase_price: int
    total_cost: int
    total_investment: int
    expected_sale_profit: int
    expected_rental_income: int
    interest_cost: int
    net_profit: int
    roi: float
    annualized_roi: float
    break_even_sale_price: int
    safety_margin: int
    disclaimer: str
