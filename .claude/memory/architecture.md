# Architecture & Data Flow

## 레이어
- `app/api/v1`: 라우터. 요청 검증 + 서비스 호출만. 비즈니스 로직 금지.
- `app/services`: 비즈니스 로직 (검색, 상세, 예측, 수익률, 위험도, 데이터품질, 정규화, 지오코딩).
- `app/repositories`: DB 접근(SQLAlchemy 쿼리) 캡슐화.
- `app/ingestion`: 외부 데이터 Connector(Mock + 실제) + 정규화 파이프라인.
- `app/models`: SQLAlchemy ORM (13개 테이블, `app/models/__init__.py`에서 전체 re-export).
- `app/schemas`: Pydantic 입출력 스키마.
- `app/workers`: Celery 앱/태스크 구조.
- `app/static/admin`: 빌드 스텝 없는 정적 관리자 웹 (`/admin`에서 서빙).

## 데이터 흐름
source raw → `raw_source_records` 저장 → 정규화(`normalization_service`) → `auction_items`/상세 upsert
→ 좌표(`geocoding_service`, MVP는 키 없으면 None) → 실거래가·낙찰사례 매칭 → 참고 낙찰가 계산(rule-v1) → 검색 API 노출

## Connector 상태
- `mock_onbid_connector.py` / `mock_real_transaction_connector.py`: 항상 사용 가능, `ENABLE_MOCK_CONNECTORS=true`(기본)일 때 우선.
- `onbid_connector.py`: 실제 공공데이터포털 "차세대 온비드" 물건목록(`getRlstCltrList2`)/물건상세(`getCltrBidInf2`) API 연동, 2026-07-11 실제 서비스키로 호출 검증 완료. `ONBID_API_KEY` 필요.
- `real_transaction_connector.py`: 실제 국토교통부 아파트매매 실거래가 상세 API(`getRTMSDataSvcAptTradeDev`) 연동, 2026-07-11 실제 서비스키로 호출 검증 완료. `MOLIT_API_KEY` + 법정동코드(LAWD_CD, 전국 250개 시/군/구 매핑) 필요.
- `court_auction_connector.py`: 인터페이스만, 크롤링 금지 원칙에 따라 `NotImplementedError`.
- `app/ingestion/pipeline.py`의 `collect_source_items(source, **connector_kwargs)`가 팩토리 선택 → fetch(kwargs 그대로 전달) → raw 저장 → 정규화 upsert → `collection_jobs` 로그를 담당. 커넥터 실패(config error/api error)는 pipeline이 잡아서 `collection_jobs.status="failed"`로 기록 — 앱 크래시 없음. `**connector_kwargs`는 국토부처럼 lawd_cd/sido+sigungu 같은 필수 파라미터가 있는 커넥터를 위한 것 (2026-07-11 추가).
- `app/ingestion/scheduler.py`의 `ScheduledJob.default_kwargs`가 `collect_all_sources_task`(수동/점검용 1회 실행 task) 실행 시 `collect_source_items`에 전달된다. `real_transaction` 항목은 예시로 서울 종로구만 기본값으로 채워둠.
- **실제 주기 실행(Celery Beat)이 연결되어 있다** (2026-07-11): `app/workers/celery_app.py`의 `beat_schedule`에 온비드(매시간, `collect_source_items_task`)와 국토부 실거래가 전국 순회(매일 새벽 3시 KST, `collect_real_transaction_all_regions_task`)가 등록됨. 전국 순회는 `real_transaction_connector.get_supported_regions()`(`_LAWD_CD_MAP` 250개 시/군/구)를 순회하며 지역당 별도 `collect_source_items` 호출 + `collection_jobs` 로그를 남긴다. `docker-compose.yml`에 `worker`/`beat` 서비스 추가되어 `docker compose up -d`로 함께 기동됨.

## 서브에이전트 매핑 (`.claude/agents/`)
- Price Prediction → `services/price_prediction_service.py` (rule-v1)
- Data Quality → `services/data_quality_service.py`
- Risk Analysis → `services/risk_analysis_service.py`

## 원칙
- 원본과 정규화 데이터 분리. 재처리 가능하게 원본 보존.
- 크롤링 대신 공식 API/제휴/Mock 우선.
- 실제 API로 수집한 원문에 개인정보가 섞일 수 있음 → `app/core/masking.py` 참고 (`conventions.md` 보안 항목).
