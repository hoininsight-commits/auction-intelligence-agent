"""기본 수익률 계산 서비스 (지시서 §7.7).

계산식은 지시서 §7.7 "계산 기준" 그대로이며 임의로 변경하지 않는다.

total_cost = 취득세 + 법무비 + 명도비 + 수리비 + 중개수수료
equity = purchase_price - loan_amount
interest_cost = loan_amount * annual_interest_rate / 100 * holding_months / 12
total_investment = equity + total_cost
expected_sale_profit = expected_sale_price - purchase_price - total_cost
expected_rental_income = monthly_rent * holding_months
net_profit = expected_sale_price - purchase_price - total_cost - interest_cost + expected_rental_income
roi = net_profit / total_investment * 100
annualized_roi = roi * 12 / holding_months
break_even_sale_price = purchase_price + total_cost + interest_cost - expected_rental_income
safety_margin = expected_sale_price - break_even_sale_price
"""
from __future__ import annotations

from app.core.disclaimers import PROFITABILITY_DISCLAIMER
from app.schemas.profitability import (
    ProfitabilityCalculateRequest,
    ProfitabilityCalculateResponse,
)


def calculate_profitability(request: ProfitabilityCalculateRequest) -> ProfitabilityCalculateResponse:
    total_cost = (
        request.acquisition_tax
        + request.legal_fee
        + request.eviction_cost
        + request.repair_cost
        + request.brokerage_fee
    )

    equity = request.purchase_price - request.loan_amount

    interest_cost = (
        request.loan_amount
        * request.annual_interest_rate
        / 100
        * request.holding_months
        / 12
    )

    total_investment = equity + total_cost

    expected_sale_profit = request.expected_sale_price - request.purchase_price - total_cost

    expected_rental_income = request.monthly_rent * request.holding_months

    net_profit = (
        request.expected_sale_price
        - request.purchase_price
        - total_cost
        - interest_cost
        + expected_rental_income
    )

    roi = (net_profit / total_investment * 100) if total_investment else 0.0

    annualized_roi = roi * 12 / request.holding_months

    break_even_sale_price = (
        request.purchase_price + total_cost + interest_cost - expected_rental_income
    )

    safety_margin = request.expected_sale_price - break_even_sale_price

    return ProfitabilityCalculateResponse(
        purchase_price=request.purchase_price,
        total_cost=round(total_cost),
        total_investment=round(total_investment),
        expected_sale_profit=round(expected_sale_profit),
        expected_rental_income=round(expected_rental_income),
        interest_cost=round(interest_cost),
        net_profit=round(net_profit),
        roi=round(roi, 2),
        annualized_roi=round(annualized_roi, 2),
        break_even_sale_price=round(break_even_sale_price),
        safety_margin=round(safety_margin),
        disclaimer=PROFITABILITY_DISCLAIMER,
    )
