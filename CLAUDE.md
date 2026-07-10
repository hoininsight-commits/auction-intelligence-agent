# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

> 원본 개발 지시서: `docs/개발지시서-v1.0.md` (PRD + 기술설계 + 작업 티켓 통합 문서). 스키마, API 응답 예시, 룰 기반 계산 공식의 1차 출처는 항상 이 문서다. 이 CLAUDE.md와 지시서가 어긋나면 지시서를 따른다.

## 프로젝트 개요

Auction Intelligence Agent — 전국 부동산 경매·공매(+ 향후 차량 공매) 정보를 통합 검색·분석하는 FastAPI 백엔드 MVP.
핵심 가치: 여러 사이트를 오가지 않고 물건 검색, 감정가/최저가/유찰이력, 인근 실거래가, 룰 기반 참고 낙찰가, 기본 수익률, 권리 위험 체크리스트를 한 곳에서 확인.

법적 리스크가 있는 크롤링(대법원 경매정보 등)은 구현하지 않는다 — 인터페이스만 설계. 실제 외부 API(온비드, 국토부 실거래가) 연동은 후순위이며, MVP는 Mock Connector로 동작한다.

## 실행 명령어 (프로젝트 골격 완성 후)

```bash
cp .env.example .env
docker compose up -d
alembic upgrade head
python -m app.seed.seed_sample_data
# http://localhost:8000/docs
```

```bash
# 테스트
pytest

# 마이그레이션 생성
alembic revision --autogenerate -m "message"
```

## 기술 스택 (고정, 임의 변경 금지)

- Python 3.11+, FastAPI, Uvicorn
- SQLAlchemy 2.x (2.x 스타일 필수, 1.x 레거시 스타일 금지)
- Alembic, PostgreSQL (+PostGIS 확장 가능 구조), Redis
- Pydantic v2
- Celery 또는 RQ (구조만, MVP는 간단 구현)
- pytest, httpx, pydantic-settings

## 아키텍처

```
app/
  core/        설정, DB 연결, 보안, 상수, 법적 고지문, 로깅
  models/      SQLAlchemy 모델 (raw ↔ 정규화 분리)
  schemas/     Pydantic v2 스키마
  api/v1/      라우터 (전부 /api/v1 prefix)
  services/    비즈니스 로직 (검색/상세/예측/수익률/관심물건/저장검색/위험도/품질/정규화/지오코딩)
  ingestion/   Connector 인터페이스 + Mock/실제 Connector + pipeline + scheduler
  repositories/ DB 접근 계층
  workers/     celery_app, tasks
  seed/        샘플 데이터 시드
alembic/       마이그레이션
tests/         pytest
```

### 데이터 흐름 원칙 (지시서 §6.1, §9.1)

1. 외부 데이터는 반드시 먼저 `raw_source_records`에 원본 그대로 저장한다.
2. 정규화 후 `auction_items`(+ `real_estate_details`/`vehicle_details`)에 upsert한다.
3. 부동산/차량 상세는 별도 테이블로 분리, 예측 결과(`price_predictions`)는 버전 관리 가능하도록 별도 테이블.
4. 수집 작업마다 `collection_jobs`에 로그를 남긴다.
5. 좌표(`latitude`/`longitude`) 필드는 항상 확보 — 추후 PostGIS 연결을 전제로 설계.

### Connector 패턴 (지시서 §9)

- `app/ingestion/base.py`의 `BaseConnector` (async `fetch_items` / `fetch_detail`)를 모든 Connector가 상속.
- `ENABLE_MOCK_CONNECTORS=true`일 때 Mock Connector 사용 (`mock_onbid_connector.py`, `mock_real_transaction_connector.py`).
- 실제 Connector(`onbid_connector.py`, `real_transaction_connector.py`, `court_auction_connector.py`)는 API 키가 없으면 동작하지 않아도 되나, 인터페이스는 반드시 구현되어 있어야 한다.
- **크롤링 구현 금지.** `court_auction_connector.py`는 인터페이스/스텁만 존재.

### 룰 기반 참고 낙찰가 (`rule-v1`, 지시서 §8)

우선순위: 유사 낙찰 사례 평균 낙찰가율 → (부족 시) 최저가 대비 평균 낙찰 배수 → (그마저 부족 시) 카테고리별 기본 낙찰가율.

보정계수 = 유찰횟수계수 × 권리위험계수 × 지역수요계수 × 시세괴리계수 (각 테이블 값은 지시서 §8.3~§8.7 그대로 사용, 임의로 튜닝하지 않는다).
신뢰도(`confidence`)가 낮으면 예측 범위를 넓힌다 (±3% → ±6%).

### 법적 고지문 (지시서 §11)

`app/core/disclaimers.py`에 상수로 정의된 `PREDICTION_DISCLAIMER` / `INVESTMENT_DISCLAIMER` / `PROFITABILITY_DISCLAIMER` / `RISK_ANALYSIS_DISCLAIMER`를 관련 API 응답에 항상 포함한다. 새 API를 추가할 때 고지문 누락이 없는지 확인할 것.

## 개발 순서 (지시서 §15, Phase 단위로 진행)

1. **Phase 1 — 골격**: FastAPI 프로젝트, Dockerfile, docker-compose.yml, pyproject.toml, 설정/DB 연결, health API
2. **Phase 2 — DB/마이그레이션**: SQLAlchemy Base + 전체 모델(14개 테이블, §6 참고), Alembic 초기 마이그레이션, seed 스크립트
3. **Phase 3 — 핵심 API**: 검색/상세/관심물건/저장검색/수익률 계산
4. **Phase 4 — 예측/분석**: 룰 기반 예측 서비스, 위험도 서비스, 데이터 품질 서비스, 관리자 API
5. **Phase 5 — 수집 기반**: Connector 인터페이스, Mock Connector 2종, raw 저장, pipeline, 수집 로그
6. **Phase 6 — 테스트/문서**: pytest, README, `.env.example`, Swagger 확인, 로컬 실행 검증

Phase 2는 Phase 1에 의존, Phase 3~5는 Phase 2 완료 후 상당 부분 병렬 가능(모델 스키마가 먼저 고정되어야 함). Phase 6은 항상 마지막.

## 완료 기준 (지시서 §16)

`docker compose up`으로 서버 기동 → `/docs` 정상 → `alembic upgrade head` 성공 → seed 삽입 → 검색/상세/예측/수익률/관심물건/저장검색/데이터품질 API 전부 동작 → `pytest` 전체 통과 → README에 실행법 명시. 이 중 하나라도 실패하면 "완료"로 보고하지 않는다.

## 코딩 규칙

- API는 전부 `/api/v1` prefix, 쿼리 파라미터/응답 필드명은 지시서 §7의 예시를 그대로 따른다 (임의로 필드명을 바꾸지 않는다).
- 인증은 MVP에서 단순화 가능 (`user_id=1` 테스트 사용자 seed).
- 실제 API 키가 없는 것을 전제로 개발 — `.env` 미설정 시에도 Mock Connector로 앱이 정상 기동해야 한다.
