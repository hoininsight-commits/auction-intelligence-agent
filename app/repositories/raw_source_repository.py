"""raw_source_records DB 접근 계층 (지시서 §6.10, §9.1).

외부 데이터는 정규화 이전에 반드시 이 저장소를 통해 raw_source_records에 원본 그대로 저장한다.
"""
from __future__ import annotations

import hashlib
import json
from typing import Any

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.masking import mask_value
from app.models.raw_source_record import RawSourceRecord


def _compute_checksum(payload: dict[str, Any]) -> str:
    """raw_payload 내용 기반 체크섬 (중복/변경 감지용)."""
    serialized = json.dumps(payload, sort_keys=True, ensure_ascii=False, default=str)
    return hashlib.sha256(serialized.encode("utf-8")).hexdigest()


class RawSourceRepository:
    def __init__(self, session: AsyncSession) -> None:
        self.session = session

    async def save_raw_record(
        self,
        *,
        source: str,
        source_record_id: str | None,
        record_type: str | None,
        raw_payload: dict[str, Any],
    ) -> RawSourceRecord:
        """원본 페이로드를 raw_source_records에 저장한다 (매 fetch마다 새 행 추가).

        저장 전 개인정보 마스킹(app.core.masking)을 적용한다 — 채무자/소유자/임차인 이름,
        연락처, 차량번호, 주민등록번호 패턴이 원문에 섞여 있어도 마스킹된 형태로만 보존한다
        (conventions.md 보안/개인정보 원칙).
        """
        masked_payload = mask_value(raw_payload)
        record = RawSourceRecord(
            source=source,
            source_record_id=source_record_id,
            record_type=record_type,
            raw_payload=masked_payload,
            checksum=_compute_checksum(masked_payload),
        )
        self.session.add(record)
        await self.session.flush()
        return record

    async def save_raw_records(
        self,
        *,
        source: str,
        record_type: str | None,
        items: list[dict[str, Any]],
        id_field: str = "source_item_id",
    ) -> list[RawSourceRecord]:
        """여러 건의 원본 아이템을 한 번에 raw_source_records에 저장한다."""
        records: list[RawSourceRecord] = []
        for item in items:
            record = await self.save_raw_record(
                source=source,
                source_record_id=str(item.get(id_field)) if item.get(id_field) is not None else None,
                record_type=record_type,
                raw_payload=item,
            )
            records.append(record)
        return records

    async def get_by_id(self, record_id: int) -> RawSourceRecord | None:
        return await self.session.get(RawSourceRecord, record_id)

    async def list_by_source(
        self, source: str, *, limit: int = 100, offset: int = 0
    ) -> list[RawSourceRecord]:
        stmt = (
            select(RawSourceRecord)
            .where(RawSourceRecord.source == source)
            .order_by(RawSourceRecord.fetched_at.desc())
            .limit(limit)
            .offset(offset)
        )
        result = await self.session.execute(stmt)
        return list(result.scalars().all())
