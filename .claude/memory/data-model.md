# Data Model 요약

## 테이블 목록 (13개, `app/models/`)
users, auction_items, real_estate_details, vehicle_details,
auction_results, price_predictions, user_watchlist, saved_searches,
raw_source_records, property_transactions, risk_assessments,
collection_jobs, notifications

## 핵심 enum 값
- source: court | onbid | private_provider | mock
- auction_type: real_estate | public_sale | vehicle
- category: apartment | villa | officetel | commercial | land | factory | vehicle
- status: active | scheduled | sold | failed | cancelled | expired | unknown
- confidence: high | medium | low
- risk_level: low | medium | high | unknown

## 제약
- user_watchlist: UNIQUE(user_id, auction_item_id) — 중복 추가 시 API가 409 반환.
- 상세/결과/예측/위험도 테이블은 auction_items(id) FK, ON DELETE CASCADE.
- notifications.auction_item_id는 ON DELETE SET NULL.
- auction_items.raw_source_record_id는 지시서 원본 SQL 그대로 FK 제약 없음(의도된 사양).
- 위/경도: NUMERIC(10,7) 유지 (PostGIS 확장 대비).
- 가격: BIGINT (원 단위).

## 예측 저장
- price_predictions: low/mid/high 가격+낙찰가율, confidence, model_version(`rule-v1`), explanation(JSONB — base_method/adjustment_factor 포함), disclaimer.

## PII 가능성 있는 필드 (마스킹 대상, conventions.md 참고)
- real_estate_details.tenant_summary / occupancy_summary / registry_summary / document_summary (자유 텍스트 — 실 API 데이터엔 임차인 이름/연락처 섞일 수 있음)
- vehicle_details.accident_history / inspection_summary (자유 텍스트 — 소유자/연락처 섞일 수 있음)
- raw_source_records.raw_payload (원문 JSON/XML — 실 커넥터 연동 시 개인정보 원문 포함 가능)
