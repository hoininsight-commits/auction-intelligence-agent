"""개인정보 마스킹 유틸 테스트 (conventions.md, .claude/commands/mask-check.md)."""

from __future__ import annotations

from app.core.masking import mask_text, mask_value


def test_mask_phone_number():
    text = "임차인 연락처: 010-1234-5678 입니다."
    masked = mask_text(text)
    assert "010-1234-5678" not in masked
    assert "[전화번호 마스킹됨]" in masked


def test_mask_resident_registration_number():
    text = "소유자 주민번호 901231-1234567 확인 필요."
    masked = mask_text(text)
    assert "901231-1234567" not in masked
    assert "[주민등록번호 마스킹됨]" in masked


def test_mask_vehicle_plate():
    text = "차량번호 12가3456 보관중."
    masked = mask_text(text)
    assert "12가3456" not in masked
    assert "[차량번호 마스킹됨]" in masked


def test_mask_named_field():
    text = "임차인: 홍길동 대항력 있음"
    masked = mask_text(text)
    assert "홍길동" not in masked
    assert "[이름 마스킹됨]" in masked


def test_mask_text_preserves_non_pii_content():
    text = "감정평가서 요약 (샘플 데이터)"
    assert mask_text(text) == text


def test_mask_value_recurses_dict_and_list():
    payload = {
        "CLTR_NM": "샘플 아파트",
        "tenant": {"phone": "010-9999-8888", "note": "임차인: 김철수"},
        "history": ["차량번호 34나5678 확인", "특이사항 없음"],
    }
    masked = mask_value(payload)
    assert masked["CLTR_NM"] == "샘플 아파트"
    assert "010-9999-8888" not in masked["tenant"]["phone"]
    assert "김철수" not in masked["tenant"]["note"]
    assert "34나5678" not in masked["history"][0]
    assert masked["history"][1] == "특이사항 없음"
