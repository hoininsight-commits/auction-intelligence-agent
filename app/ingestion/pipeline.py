"""raw 저장 -> 정규화 -> upsert 파이프라인 (지시서 §9.5).

`collect_source_items(source)`가 핵심 진입점이다:
    1. connector 선택 (ENABLE_MOCK_CONNECTORS에 따라 mock/real 결정)
    2. fetch_items 실행
    3. raw_source_records 저장
    4. auction_items(경매/공매) 또는 property_transactions(실거래가) 정규화 및 upsert
    5. collection_jobs 로그 저장
"""
from __future__ import annotations

from datetime import datetime, timezone
from typing import Any

from app.core.config import settings
from app.core.database import AsyncSessionLocal
from app.core.logging import get_logger
from app.ingestion.base import BaseConnector
from app.ingestion.court_auction_connector import CourtAuctionConnector
from app.ingestion.mock_onbid_connector import MockOnbidConnector
from app.ingestion.mock_real_transaction_connector import MockRealTransactionConnector
from app.ingestion.onbid_connector import OnbidConnector
from app.ingestion.real_transaction_connector import RealTransactionConnector
from app.models.collection_job import CollectionJob
from app.repositories.raw_source_repository import RawSourceRepository
from app.services.normalization_service import NormalizationService

logger = get_logger(__name__)


def _utcnow_naive() -> datetime:
    """DB timestamp 컬럼이 timezone-naive이므로 tz 정보를 제거한 UTC 시각을 반환한다."""
    return datetime.now(timezone.utc).replace(tzinfo=None)

# pipeline에서 사용하는 "논리적" source 이름 -> 실제 connector.source 매핑을 위한 별칭.
_ONBID_ALIASES = {"onbid"}
_REAL_TRANSACTION_ALIASES = {"real_transaction", "molit", "molit_mock", "mock_real_transaction"}
_COURT_ALIASES = {"court"}


def get_connector(source: str) -> BaseConnector:
    """source 이름과 ENABLE_MOCK_CONNECTORS 설정에 따라 알맞은 Connector 인스턴스를 반환한다.

    지시서 §9.1: API 키가 없으면 Mock Connector를 사용한다.
    """
    normalized = source.lower()

    if normalized in _ONBID_ALIASES:
        if settings.ENABLE_MOCK_CONNECTORS:
            return MockOnbidConnector()
        return OnbidConnector()

    if normalized in _REAL_TRANSACTION_ALIASES:
        if settings.ENABLE_MOCK_CONNECTORS:
            return MockRealTransactionConnector()
        return RealTransactionConnector()

    if normalized in _COURT_ALIASES:
        return CourtAuctionConnector()

    raise ValueError(f"알 수 없는 데이터 수집 source 입니다: {source}")


def _is_property_transaction_item(item: dict[str, Any]) -> bool:
    """실거래가(property_transactions) 레코드인지 경매/공매(auction_items) 레코드인지 판별한다.

    실거래가 원본(§9.4)은 deal_price를 갖고, 경매/공매 원본(§9.3)은 appraisal_price/
    minimum_price를 갖는다.
    """
    return "deal_price" in item and "appraisal_price" not in item


async def collect_source_items(source: str) -> dict[str, Any]:
    """단일 source에 대한 전체 수집 파이프라인을 실행한다.

    1. connector 선택
    2. fetch_items 실행
    3. raw_source_records 저장
    4. auction_items 정규화 및 upsert (property_transactions 소스는 해당 테이블에 upsert)
    5. collection_jobs 로그 저장
    """
    started_at = _utcnow_naive()

    async with AsyncSessionLocal() as session:
        job = CollectionJob(
            source=source,
            job_type="fetch_items",
            status="running",
            started_at=started_at,
        )
        session.add(job)
        await session.flush()

        fetched_count = 0
        inserted_count = 0
        updated_count = 0
        failed_count = 0
        error_message: str | None = None
        status = "success"

        try:
            connector = get_connector(source)
            items = await connector.fetch_items()
            fetched_count = len(items)

            raw_repo = RawSourceRepository(session)
            normalization_service = NormalizationService(session)

            for item in items:
                try:
                    is_transaction = _is_property_transaction_item(item)
                    record_type = "property_transaction" if is_transaction else "auction_item"
                    item_source = item.get("source", connector.source)
                    id_field = "source_item_id" if not is_transaction else None

                    raw_record = await raw_repo.save_raw_record(
                        source=item_source,
                        source_record_id=(
                            str(item.get(id_field)) if id_field and item.get(id_field) else None
                        ),
                        record_type=record_type,
                        raw_payload=item,
                    )

                    if is_transaction:
                        _, created = await normalization_service.upsert_property_transaction(item)
                    else:
                        _, created = await normalization_service.upsert_auction_item(
                            item, raw_source_record_id=raw_record.id
                        )

                    if created:
                        inserted_count += 1
                    else:
                        updated_count += 1
                except Exception:
                    failed_count += 1
                    logger.exception("Failed to normalize item from source=%s", source)

        except Exception as exc:  # connector 선택/fetch_items 자체가 실패한 경우
            status = "failed"
            error_message = str(exc)
            logger.exception("collect_source_items failed for source=%s", source)
        else:
            status = "success" if failed_count == 0 else "partial_success"

        job.status = status
        job.fetched_count = fetched_count
        job.inserted_count = inserted_count
        job.updated_count = updated_count
        job.failed_count = failed_count
        job.error_message = error_message
        job.finished_at = _utcnow_naive()

        await session.commit()

        return {
            "source": source,
            "job_id": job.id,
            "status": status,
            "fetched_count": fetched_count,
            "inserted_count": inserted_count,
            "updated_count": updated_count,
            "failed_count": failed_count,
            "error_message": error_message,
        }
