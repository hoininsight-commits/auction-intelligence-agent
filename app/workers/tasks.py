"""비동기 수집 작업 태스크.

MVP에서는 Celery 구조만 잡고, 실제 작업(수집 파이프라인 실행)은 간단히 구현한다
(지시서 §1). `app.ingestion.pipeline.collect_source_items`는 async 함수이므로
Celery task 내부에서 `asyncio.run`으로 감싸서 실행한다.
"""
from __future__ import annotations

import asyncio
from typing import Any

from app.ingestion.pipeline import collect_source_items
from app.workers.celery_app import celery_app


@celery_app.task(name="app.workers.tasks.collect_source_items_task")
def collect_source_items_task(source: str) -> dict[str, Any]:
    """단일 source에 대해 `collect_source_items`를 실행하는 Celery task."""
    return asyncio.run(collect_source_items(source))


@celery_app.task(name="app.workers.tasks.collect_all_sources_task")
def collect_all_sources_task() -> list[dict[str, Any]]:
    """스케줄에 정의된 모든 source에 대해 순차적으로 수집을 실행하는 Celery task."""
    from app.ingestion.scheduler import get_schedule

    results = []
    for scheduled_job in get_schedule():
        results.append(asyncio.run(collect_source_items(scheduled_job.source)))
    return results
