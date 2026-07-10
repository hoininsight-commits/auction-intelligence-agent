"""애플리케이션 설정 (지시서 §4 환경 변수 반영).

Phase 1: 설정 골격만 구현. DB/Redis 연결에 사용되는 값만 실제로 사용되며,
나머지(API 키 등)는 Phase 5 Connector 구현에서 사용된다.
"""
from functools import lru_cache

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=True,
        extra="ignore",
    )

    APP_NAME: str = "Auction Intelligence Agent"
    APP_ENV: str = "local"
    DEBUG: bool = True

    DATABASE_URL: str = (
        "postgresql+psycopg://auction:auction@postgres:5432/auction_db"
    )
    TEST_DATABASE_URL: str = (
        "postgresql+psycopg://auction:auction@postgres:5432/auction_test_db"
    )

    REDIS_URL: str = "redis://redis:6379/0"

    SECRET_KEY: str = "change-me"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 1440

    ONBID_API_KEY: str = ""
    MOLIT_API_KEY: str = ""
    PUBLIC_DATA_API_KEY: str = ""
    KAKAO_MAP_API_KEY: str = ""
    NAVER_MAP_API_KEY: str = ""

    ENABLE_MOCK_CONNECTORS: bool = True

    @property
    def async_database_url(self) -> str:
        """asyncpg 드라이버를 사용하는 async SQLAlchemy 엔진용 URL로 변환."""
        if self.DATABASE_URL.startswith("postgresql+psycopg://"):
            return self.DATABASE_URL.replace(
                "postgresql+psycopg://", "postgresql+asyncpg://", 1
            )
        if self.DATABASE_URL.startswith("postgresql://"):
            return self.DATABASE_URL.replace(
                "postgresql://", "postgresql+asyncpg://", 1
            )
        return self.DATABASE_URL


@lru_cache
def get_settings() -> Settings:
    return Settings()


settings = get_settings()
