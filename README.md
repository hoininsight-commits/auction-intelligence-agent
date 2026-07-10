# Auction Intelligence Agent

## Overview

전국 경매·공매(부동산 + 차량) 물건 검색, 룰 기반 참고 낙찰가 계산, 관심 물건 저장,
저장 검색, 기본 수익률 계산, 데이터 품질 점검 기능을 제공하는 FastAPI 백엔드 MVP입니다.

핵심 가치: 여러 사이트를 오가지 않고 물건 검색, 감정가/최저가/유찰이력, 인근 실거래가,
룰 기반 참고 낙찰가, 기본 수익률, 권리 위험 체크리스트를 한 곳에서 확인할 수 있습니다.

법적 리스크가 있는 크롤링(대법원 경매정보 등)은 구현하지 않았습니다 — 인터페이스만 설계되어
있습니다. 실제 외부 API(온비드, 국토부 실거래가) 연동은 후순위이며, 이 MVP는 Mock Connector로
동작합니다 (`ENABLE_MOCK_CONNECTORS=true`).

## Tech Stack

- Python 3.11+, FastAPI, Uvicorn
- SQLAlchemy 2.x (async, asyncpg / psycopg 드라이버)
- Alembic, PostgreSQL, Redis
- Pydantic v2, pydantic-settings
- Celery (구조만 구현, MVP는 워커 없이도 동작)
- pytest, pytest-asyncio, httpx

## Quick Start

### Docker Compose (권장)

```bash
cp .env.example .env
docker compose up -d
alembic upgrade head
python -m app.seed.seed_sample_data
# http://localhost:8000/docs
# 관리자 페이지: http://localhost:8000/admin
```

### Docker 없이 로컬에서 실행

Docker가 없는 환경(예: 로컬에 PostgreSQL을 직접 설치한 경우)에서는 아래처럼
`DATABASE_URL`의 host를 `localhost`로 지정해 실행할 수 있습니다.

```bash
python -m venv .venv && source .venv/bin/activate
pip install -e ".[dev]"

cp .env.example .env
# .env의 DATABASE_URL / TEST_DATABASE_URL host를 postgres -> localhost로 수정
# (또는 실행 시 환경변수로 덮어쓰기)

export DATABASE_URL="postgresql+psycopg://auction:auction@localhost:5432/auction_db"
alembic upgrade head
python -m app.seed.seed_sample_data

uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload
# http://localhost:8000/docs
```

### 테스트

실제 PostgreSQL 테스트 DB(`.env`의 `TEST_DATABASE_URL`, 기본값은 `auction_test_db`)를
사용합니다. 테스트 세션 시작 시 스키마를 재생성하고, 테스트마다 데이터를 TRUNCATE하여
격리합니다. `docker compose up`이 만드는 DB는 `POSTGRES_DB`(기본 `auction_db`) 하나뿐이라,
테스트 DB는 최초 1회 직접 생성해야 합니다.

```bash
docker compose exec postgres psql -U auction -d auction_db -c "CREATE DATABASE auction_test_db;"
pytest
```

## API

| Method | Path | 설명 |
|---|---|---|
| GET | `/api/v1/health` | 헬스 체크 |
| GET | `/api/v1/auction-items` | 경매·공매 물건 검색 (지역/카테고리/가격/유찰횟수/정렬/페이지네이션) |
| GET | `/api/v1/auction-items/{id}` | 물건 상세 (예측가, 위험도, 인근 실거래가, 고지문 포함) |
| POST | `/api/v1/auction-items/{id}/predict-price` | 룰 기반(rule-v1) 참고 낙찰가 계산 |
| POST | `/api/v1/watchlist` | 관심 물건 추가 |
| GET | `/api/v1/watchlist` | 관심 물건 목록 (`user_id` 쿼리 필수) |
| DELETE | `/api/v1/watchlist/{auction_item_id}` | 관심 물건 삭제 (`user_id` 쿼리 필수) |
| POST | `/api/v1/saved-searches` | 저장 검색 생성 |
| GET | `/api/v1/saved-searches` | 저장 검색 목록 (`user_id` 쿼리 필수) |
| PUT | `/api/v1/saved-searches/{id}` | 저장 검색 수정 |
| DELETE | `/api/v1/saved-searches/{id}` | 저장 검색 삭제 (`user_id` 쿼리 필수) |
| POST | `/api/v1/profitability/calculate` | 기본 수익률(ROI, 손익분기 매도가 등) 계산 |
| GET | `/api/v1/admin/data-quality/summary` | 데이터 품질 요약 (감정가/좌표 누락, 중복 사건번호 등) |

전체 스키마와 예시는 서버 기동 후 `/docs` (Swagger UI)에서 확인할 수 있습니다.

MVP에서는 인증을 단순화하여 `user_id=1` 테스트 사용자(seed 데이터로 자동 생성)를 사용합니다.

## Legal Disclaimer

본 서비스의 예상 낙찰가, 수익률, 권리분석, 위험도 정보는 참고용입니다. 실제 입찰 및 투자
결정은 사용자의 책임이며, 입찰 전 법무사·변호사·세무사 등 전문가 검토를 권장합니다. 본
서비스는 낙찰 결과나 투자 수익을 보장하지 않습니다.

## 알려진 문서 불일치 (참고)

원본 개발지시서 §7.7(기본 수익률 계산 API)의 응답 예시 값 중 `safety_margin: 42,000,000`은
지시서 자체가 정의한 공식(`safety_margin = expected_sale_price - break_even_sale_price`)으로
재계산하면 일치하지 않습니다(공식대로 계산하면 다른 값이 나옵니다). 실제 구현
(`app/services/profitability_service.py`)과 이 README의 테스트는 지시서의 "예시 숫자"가
아니라 지시서가 명시한 "계산 공식"을 그대로 따릅니다.
