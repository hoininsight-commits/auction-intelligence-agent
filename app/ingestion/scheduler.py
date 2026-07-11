"""수집 작업 스케줄러.

MVP 스텁: 실제 스케줄링 트리거(cron, celery beat 등)는 구현하지 않는다.
어떤 source를 어떤 주기로 수집해야 하는지 구조만 정의해 두고,
실제 트리거는 후속 작업(celery beat 설정 등)에서 연결한다.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any


@dataclass(frozen=True)
class ScheduledJob:
    source: str
    interval_minutes: int
    description: str = ""
    # collect_source_items(source, **default_kwargs)로 그대로 전달된다.
    # 국토부 실거래가 커넥터처럼 lawd_cd/sido+sigungu 등 필수 파라미터가 있는
    # source는 여기에 기본값을 채워둬야 스케줄 실행 시 config error 없이 동작한다.
    default_kwargs: dict[str, Any] = field(default_factory=dict)


# MVP 수준의 수집 스케줄 정의. 실제 트리거(celery beat schedule 등)는 아직 연결하지 않는다.
DEFAULT_SCHEDULE: list[ScheduledJob] = [
    ScheduledJob(source="onbid", interval_minutes=60, description="온비드 공매 물건 수집"),
    ScheduledJob(
        source="real_transaction",
        interval_minutes=60 * 24,
        description=(
            "국토부 실거래가 수집. 전국 250개 시/군/구를 모두 순회하는 로직은 아직 "
            "없어 예시로 서울 종로구만 기본 대상으로 지정해 둔다 — 전국 수집은 "
            "_LAWD_CD_MAP을 순회하는 반복 로직을 별도로 구현해야 한다."
        ),
        default_kwargs={"sido": "서울특별시", "sigungu": "종로구"},
    ),
]


def get_schedule() -> list[ScheduledJob]:
    """현재 정의된 수집 스케줄을 반환한다. (트리거 로직은 후속 작업에서 구현)"""
    return list(DEFAULT_SCHEDULE)
