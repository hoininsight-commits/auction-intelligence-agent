"""pytest fixture 설정 (지시서 §13).

- 실제 Postgres 테스트 DB를 사용한다. `.env`의 `TEST_DATABASE_URL`이 가리키는
  `auction_test_db`를 기준으로 하되, 로컬(비 Docker) 환경에서는 host를
  `localhost`로 덮어써서 사용한다 (docker-compose 환경에서는 host가 `postgres`).
- 아래 환경변수 override는 `app.core.config`가 import되어 `Settings()`가
  인스턴스화되기 *전에* 반드시 실행되어야 한다 (pydantic-settings는
  os.environ 값을 .env 파일보다 우선한다).
- 세션 시작 시 스키마를 1회 재생성하고, 매 테스트 종료 후 전체 테이블을
  TRUNCATE하여 테스트 간 데이터가 섞이지 않도록 한다.
"""
from __future__ import annotations

import os

_DEFAULT_TEST_DATABASE_URL = "postgresql+psycopg://auction:auction@localhost:5432/auction_test_db"

# docker-compose 없이 로컬에서 pytest를 실행하는 경우를 기본값으로 하되,
# 이미 환경변수로 TEST_DATABASE_URL / DATABASE_URL이 설정되어 있으면 존중한다.
os.environ.setdefault("TEST_DATABASE_URL", _DEFAULT_TEST_DATABASE_URL)
os.environ.setdefault("DATABASE_URL", os.environ["TEST_DATABASE_URL"])

from collections.abc import AsyncGenerator  # noqa: E402

import pytest_asyncio  # noqa: E402
from httpx import ASGITransport, AsyncClient  # noqa: E402
from sqlalchemy import text  # noqa: E402
from sqlalchemy.ext.asyncio import AsyncSession  # noqa: E402

from app.core.constants import TEST_USER_EMAIL, TEST_USER_ID, TEST_USER_NICKNAME  # noqa: E402
from app.core.database import AsyncSessionLocal, engine  # noqa: E402
from app.main import app  # noqa: E402
from app.models import Base, User  # noqa: E402


@pytest_asyncio.fixture(scope="session", autouse=True)
async def _prepare_schema() -> AsyncGenerator[None, None]:
    """세션 시작 시 1회, 실제 Postgres 테스트 DB에 전체 스키마를 재생성한다."""
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)
        await conn.run_sync(Base.metadata.create_all)
    yield
    await engine.dispose()


@pytest_asyncio.fixture(autouse=True)
async def _clean_tables(_prepare_schema: None) -> AsyncGenerator[None, None]:
    """각 테스트 종료 후 모든 테이블을 TRUNCATE하여 다음 테스트에 영향을 주지 않는다."""
    yield
    async with engine.begin() as conn:
        table_names = ", ".join(f'"{t.name}"' for t in reversed(Base.metadata.sorted_tables))
        await conn.execute(text(f"TRUNCATE TABLE {table_names} RESTART IDENTITY CASCADE"))


@pytest_asyncio.fixture
async def db_session() -> AsyncGenerator[AsyncSession, None]:
    """테스트에서 직접 데이터를 seed하기 위한 DB 세션."""
    async with AsyncSessionLocal() as session:
        yield session


@pytest_asyncio.fixture
async def client() -> AsyncGenerator[AsyncClient, None]:
    """FastAPI 앱에 대한 httpx AsyncClient (ASGITransport, 실제 서버 기동 없이 호출)."""
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        yield ac


@pytest_asyncio.fixture
async def test_user(db_session: AsyncSession) -> User:
    """관심 물건/저장 검색 테스트에서 공용으로 쓰는 테스트 사용자 (id=1, security.py의 TEST_USER_ID와 동일)."""
    user = User(
        id=TEST_USER_ID,
        email=TEST_USER_EMAIL,
        nickname=TEST_USER_NICKNAME,
        is_active=True,
        is_admin=False,
    )
    db_session.add(user)
    await db_session.commit()
    await db_session.refresh(user)
    return user
