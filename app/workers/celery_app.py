"""Celery 워커 앱 설정.

MVP에서는 Celery 구조만 잡는다 (지시서 §1). REDIS_URL을 broker/backend로 사용하며,
실제 스케줄 트리거(celery beat)는 app/ingestion/scheduler.py에 구조만 정의되어 있다.
"""
from __future__ import annotations

from celery import Celery

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
)
