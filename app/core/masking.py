"""개인정보 마스킹 유틸 (conventions.md 보안/개인정보 원칙).

채무자·소유자·임차인 이름, 차량번호, 연락처, 주민등록 관련 정보를 저장 전에 마스킹한다.
정규식 기반 패턴 매칭이므로 완벽한 개인정보 탐지는 보장하지 않는다 — 알려진 형식(전화번호,
주민등록번호, 한국 차량번호판, "라벨: 이름" 형태의 성명 표기)만 다룬다. `/mask-check` 커맨드로
누락 여부를 주기적으로 점검한다.
"""

from __future__ import annotations

import re
from typing import Any

_PHONE_PATTERN = re.compile(r"(?:\+?82[-\s]?)?0(?:2|1\d|[3-6]\d|70)[-\s]?\d{3,4}[-\s]?\d{4}")

_RRN_PATTERN = re.compile(r"\b\d{6}[-\s]?[1-4]\d{6}\b")

# 한국 차량 번호판: "12가3456", "123가4567", 지역명 포함 "서울12가3456" 등
_VEHICLE_PLATE_PATTERN = re.compile(r"(?:[가-힣]{2}\s?)?\d{2,3}\s?[가-힣]\s?\d{4}")

_NAME_LABELS = ("임차인", "소유자", "채무자", "점유자", "성명", "이름", "명의자")
_NAME_LABEL_PATTERN = re.compile(
    rf"(?P<label>{'|'.join(_NAME_LABELS)})\s*[:：]?\s*(?P<name>[가-힣]{{2,4}})(?=\s|$|[,.)])"
)


def mask_phone_number(text: str) -> str:
    return _PHONE_PATTERN.sub("[전화번호 마스킹됨]", text)


def mask_resident_registration_number(text: str) -> str:
    return _RRN_PATTERN.sub("[주민등록번호 마스킹됨]", text)


def mask_vehicle_plate(text: str) -> str:
    return _VEHICLE_PLATE_PATTERN.sub("[차량번호 마스킹됨]", text)


def mask_named_fields(text: str) -> str:
    return _NAME_LABEL_PATTERN.sub(lambda m: f"{m.group('label')}: [이름 마스킹됨]", text)


def mask_text(text: str) -> str:
    """문자열 하나에 모든 마스킹 규칙을 순서대로 적용한다."""
    if not text:
        return text
    masked = text
    # RRN은 전화번호 패턴보다 먼저 처리해야 숫자열이 잘못 잘려 매칭되지 않는다.
    masked = mask_resident_registration_number(masked)
    masked = mask_phone_number(masked)
    masked = mask_vehicle_plate(masked)
    masked = mask_named_fields(masked)
    return masked


def mask_value(value: Any) -> Any:
    """dict/list/str을 재귀적으로 순회하며 문자열 값에 마스킹을 적용한다.

    raw_source_records.raw_payload처럼 구조를 알 수 없는 원본 JSON/XML 파싱 결과에 사용한다.
    """
    if isinstance(value, str):
        return mask_text(value)
    if isinstance(value, dict):
        return {key: mask_value(v) for key, v in value.items()}
    if isinstance(value, list):
        return [mask_value(v) for v in value]
    return value
