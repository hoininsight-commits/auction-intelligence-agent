"""SQLAlchemy 2.x Declarative Base (지시서 §6).

모든 모델은 이 Base를 상속한다. Alembic의 target_metadata도 이 Base.metadata를 참조한다.
"""

from sqlalchemy.orm import DeclarativeBase


class Base(DeclarativeBase):
    """모든 ORM 모델의 공통 베이스 클래스."""
