"""SQLAlchemy 2.x 비동기 엔진/세션 설정.

Phase 1: 엔진/세션/FastAPI 의존성(get_db)만 구성한다.
실제 테이블 모델(Base의 하위 클래스)은 Phase 2에서 app/models/base.py에 정의된다.
"""
from collections.abc import AsyncGenerator

from sqlalchemy.ext.asyncio import (
    AsyncEngine,
    AsyncSession,
    async_sessionmaker,
    create_async_engine,
)

from app.core.config import settings

engine: AsyncEngine = create_async_engine(
    settings.async_database_url,
    echo=settings.DEBUG,
    pool_pre_ping=True,
)

AsyncSessionLocal = async_sessionmaker(
    bind=engine,
    class_=AsyncSession,
    expire_on_commit=False,
    autoflush=False,
)


async def get_db() -> AsyncGenerator[AsyncSession, None]:
    """FastAPI dependency: 요청 스코프 비동기 DB 세션을 제공한다."""
    async with AsyncSessionLocal() as session:
        yield session
