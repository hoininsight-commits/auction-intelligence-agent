"""수집 작업 스케줄러.

MVP 스텁: 실제 스케줄링 트리거(cron, celery beat 등)는 구현하지 않는다.
어떤 source를 어떤 주기로 수집해야 하는지 구조만 정의해 두고,
실제 트리거는 후속 작업(celery beat 설정 등)에서 연결한다.
"""

from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class ScheduledJob:
    source: str
    interval_minutes: int
    description: str = ""


# MVP 수준의 수집 스케줄 정의. 실제 트리거(celery beat schedule 등)는 아직 연결하지 않는다.
DEFAULT_SCHEDULE: list[ScheduledJob] = [
    ScheduledJob(source="onbid", interval_minutes=60, description="온비드 공매 물건 수집"),
    ScheduledJob(
        source="real_transaction",
        interval_minutes=60 * 24,
        description="국토부 실거래가 수집",
    ),
]


def get_schedule() -> list[ScheduledJob]:
    """현재 정의된 수집 스케줄을 반환한다. (트리거 로직은 후속 작업에서 구현)"""
    return list(DEFAULT_SCHEDULE)
