"""raw source / 수집 관련 Pydantic v2 스키마 (지시서 §9).

Phase 5에서 구현 예정 (Phase 1은 프로젝트 골격만 담당).

DataQualitySummaryResponse는 Phase 4 관리자 데이터 품질 API(지시서 §7.8, §10)용 스키마다.
"""
from __future__ import annotations

from pydantic import BaseModel


class DataQualitySummaryResponse(BaseModel):
    """GET /api/v1/admin/data-quality/summary 응답 (지시서 §7.8 응답 예시 기준).

    §10의 8개 검증 항목을 모두 반영한다. missing_address / invalid_minimum_price_over_appraisal은
    §7.8 예시에는 없지만 §10 검증 항목(3, 5)을 그대로 노출하기 위해 추가한 필드다.
    """

    total_items: int
    missing_appraisal_price: int
    missing_minimum_price: int
    missing_coordinates: int
    past_bid_date_active_status: int
    duplicate_case_numbers: int
    prediction_missing: int

    # §10 항목 3, 5 (지시서 §7.8 예시에는 없지만 §10 요구사항 충족을 위해 추가)
    invalid_minimum_price_over_appraisal: int
    missing_address: int
