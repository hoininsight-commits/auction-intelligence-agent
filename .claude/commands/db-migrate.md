# /db-migrate

DB 스키마 변경을 마이그레이션한다.

작업:
1. 모델 변경 확인.
2. `alembic revision --autogenerate -m "<메시지>"`
3. 생성된 마이그레이션 파일을 검토 (autogenerate 오탐 점검).
4. `alembic upgrade head`
5. 필요 시 seed 재실행.

규칙:
- autogenerate 결과를 맹신하지 말고 diff를 사람이 읽기 좋게 요약.
- 파괴적 변경(drop)은 경고 표시.