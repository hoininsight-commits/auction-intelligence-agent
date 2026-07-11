"""Celery 워커 앱 설정.

REDIS_URL을 broker/backend로 사용한다. 실제 주기 실행은 celery beat로 트리거되며,
`beat_schedule`에 온비드(매시간)/국토부 실거래가 전국 순회(매일 새벽 3시) 작업이
등록되어 있다. 컨테이너로는 `celery -A app.workers.celery_app worker`와
`celery -A app.workers.celery_app beat`를 각각 별도 프로세스로 띄워야 한다
(docker-compose.yml의 worker/beat 서비스 참고).
"""

from __future__ import annotations

from celery import Celery
from celery.schedules import crontab

from app.core.config import settings

celery_app = Celery(
    "auction_intelligence_agent",
    broker=settings.REDIS_URL,
    backend=settings.REDIS_URL,
    include=["app.workers.tasks"],
)

celery_app.conf.update(
    task_serializer="json",
    accept_content=["json"],
    result_serializer="json",
    timezone="Asia/Seoul",
    enable_utc=True,
    beat_schedule={
        "collect-onbid-hourly": {
            "task": "app.workers.tasks.collect_source_items_task",
            "schedule": 60 * 60,
            "args": ("onbid",),
        },
        "collect-real-transaction-nationwide-daily": {
            "task": "app.workers.tasks.collect_real_transaction_all_regions_task",
            "schedule": crontab(hour=3, minute=0),
        },
    },
)
