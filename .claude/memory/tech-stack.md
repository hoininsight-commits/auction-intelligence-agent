# Tech Stack (고정 규칙)

## 언어/런타임
- Python 3.11 이상 (컨테이너는 3.11-slim)

## 백엔드
- FastAPI + Uvicorn
- SQLAlchemy 2.x (async, declarative, typed `Mapped[]`) + asyncpg
- Alembic (마이그레이션)
- Pydantic v2 / pydantic-settings
- httpx (외부 API 클라이언트 — 온비드/국토부 실거래가 실연동에 사용 중)

## 데이터
- PostgreSQL 16 (PostGIS 확장 가능 구조로 위/경도 컬럼 유지)
- Redis 7 (캐시, Celery 브로커)
- Celery — 구조는 완성(`app/workers/`), 실제 스케줄 트리거는 MVP 스텁 수준

## 테스트/품질
- pytest + pytest-asyncio (session-scope event loop, `tests/conftest.py`)
- ruff (lint/format) — 도입 예정, `pyproject.toml`의 `[tool.ruff]` 참고

## 인프라
- Docker + docker-compose (app/postgres/redis) — 실제 Docker Desktop으로 `docker compose up` 검증 완료

## 금지
- 크롤링 라이브러리 기반 수집 코드(Playwright/BS4 등) 구현 금지 — `app/ingestion/court_auction_connector.py`는 인터페이스만 존재, `NotImplementedError`.
