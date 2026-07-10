# Conventions (코딩/보안/고지)

## 코딩
- 함수/변수 snake_case, 클래스 PascalCase.
- 서비스는 순수 함수 지향, DB 세션은 의존성 주입(`app/api/deps.py`의 `get_db`).
- 모든 응답 스키마는 Pydantic v2 모델로 명시.
- 매직넘버 금지 → `app/core/constants.py`로 (rule-v1 계수 테이블 전부 여기 있음).

## 보안/개인정보
- 채무자·소유자·임차인 이름, 차량번호, 연락처, 주민등록 관련 정보는 저장 시 마스킹한다.
- 마스킹 유틸: `app/core/masking.py` — 전화번호/차량번호판/주민등록번호 패턴 정규식 마스킹.
- 실제 온비드/국토부 API로 수집한 원문(raw_source_records)과 정규화된 상세 텍스트(real_estate_details의 tenant_summary/occupancy_summary, vehicle_details의 accident_history 등)는 저장 전 마스킹을 거친다 (`normalization_service.py`에서 적용).
- 최소 수집 원칙. 불필요한 개인정보는 저장하지 않는다.
- `/mask-check` 커맨드로 마스킹 누락 점검.

## 법적 고지 (필수 포함, `app/core/disclaimers.py`에 단일 정의)
- 예측 응답(`POST /predict-price`) → `PREDICTION_DISCLAIMER`
- 수익률 응답(`POST /profitability/calculate`) → `PROFITABILITY_DISCLAIMER`
- 위험도(`risk_assessment` 필드) → `RISK_ANALYSIS_DISCLAIMER`
- 상세/투자정보(`GET /auction-items/{id}`) → `INVESTMENT_DISCLAIMER`

## 알려진 지시서 오류
- §7.7 수익률 API 응답 예시의 `safety_margin: 42,000,000`은 지시서 자신의 공식(`expected_sale_price - break_even_sale_price`)과 맞지 않는 예시 오류. 코드는 공식 기준으로 구현되어 있고, 이게 맞는 것으로 결정됨(사용자 확인 완료).

## 커밋
- 작업 단위로 작게 커밋. 메시지는 한국어, 무엇을/왜 중심.
- 매 기능 완료 시 커밋 + `git push` (이 프로젝트는 GitHub 원격 연결됨: `hoininsight-commits/auction-intelligence-agent`).
