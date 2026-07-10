"""보안 관련 유틸리티 (스텁).

MVP에서는 인증을 단순화하여 `user_id=1` 테스트 사용자를 사용한다
(지시서 "코딩 규칙" 참고). 실제 토큰 발급/검증 로직은 필요 시 이후 phase에서 확장한다.
"""

from app.core.constants import TEST_USER_ID


def get_current_user_id() -> int:
    """MVP 스텁: 항상 테스트 사용자 ID를 반환한다."""
    return TEST_USER_ID
