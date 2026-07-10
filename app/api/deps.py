"""FastAPI 공용 의존성."""
from collections.abc import AsyncGenerator

from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.core.security import get_current_user_id

__all__ = ["get_db", "get_current_user_id"]


async def get_db_session() -> AsyncGenerator[AsyncSession, None]:
    """get_db의 별칭. Phase 3+ 라우터에서 Depends(get_db_session)로 사용."""
    async for session in get_db():
        yield session
