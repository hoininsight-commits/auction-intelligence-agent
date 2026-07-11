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
def collect_source_items_task(source: str, **connector_kwargs: Any) -> dict[str, Any]:
    """단일 source에 대해 `collect_source_items`를 실행하는 Celery task.

    connector_kwargs는 그대로 connector.fetch_items()에 전달된다 (예: 국토부
    실거래가 커넥터의 lawd_cd/sido+sigungu, deal_ymd).
    """
    return asyncio.run(collect_source_items(source, **connector_kwargs))


@celery_app.task(name="app.workers.tasks.collect_all_sources_task")
def collect_all_sources_task() -> list[dict[str, Any]]:
    """스케줄에 정의된 모든 source에 대해 1회씩 순차 수집하는 수동/점검용 Celery task.

    `get_schedule()`의 `default_kwargs`(예: real_transaction은 서울 종로구 1개
    지역)만 사용하는 간단한 버전이다. 국토부 실거래가를 전국 단위로 순회하려면
    `collect_real_transaction_all_regions_task`를 사용한다.
    """
    from app.ingestion.scheduler import get_schedule

    results = []
    for scheduled_job in get_schedule():
        results.append(
            asyncio.run(collect_source_items(scheduled_job.source, **scheduled_job.default_kwargs))
        )
    return results


async def _collect_real_transaction_all_regions(deal_ymd: str | None) -> list[dict[str, Any]]:
    from app.ingestion.real_transaction_connector import get_supported_regions

    results: list[dict[str, Any]] = []
    for sido, sigungu in get_supported_regions():
        kwargs: dict[str, Any] = {"sido": sido}
        if sigungu:
            kwargs["sigungu"] = sigungu
        if deal_ymd:
            kwargs["deal_ymd"] = deal_ymd
        try:
            result = await collect_source_items("real_transaction", **kwargs)
        except Exception as exc:
            # 방어적 처리: 한 지역의 예상 밖 예외로 전체 순회가 중단되지 않도록 함
            result = {
                "source": "real_transaction",
                "sido": sido,
                "sigungu": sigungu,
                "status": "failed",
                "error_message": str(exc),
            }
        results.append(result)
    return results


@celery_app.task(name="app.workers.tasks.collect_real_transaction_all_regions_task")
def collect_real_transaction_all_regions_task(deal_ymd: str | None = None) -> list[dict[str, Any]]:
    """국토부 실거래가를 `_LAWD_CD_MAP`에 등록된 전국 250개 시/군/구 전체에 대해
    순회 수집하는 Celery task. 지역 하나당 별도 collect_source_items 호출(및
    별도 collection_jobs 로그)이 생성된다. deal_ymd 미지정 시 각 호출은 커넥터
    기본값(이번 달)을 사용한다.
    """
    return asyncio.run(_collect_real_transaction_all_regions(deal_ymd))
