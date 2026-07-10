# Definition of Done (MVP 완료 기준)

1. docker compose up 으로 서버 실행. — ✅ 실제 Docker Desktop으로 검증됨
2. /docs 에서 Swagger 문서 열림. — ✅
3. Alembic 마이그레이션 정상 실행. — ✅
4. Seed 데이터 삽입됨. — ✅
5. 검색 API가 샘플 물건 반환. — ✅
6. 상세 API가 예측값+고지문 포함. — ✅
7. 예측 API가 룰 기반 참고 낙찰가 생성. — ✅ (3단계 fallback 전부 실동작 확인)
8. 수익률 계산 API 정상 동작. — ✅
9. 관심물건 추가/조회/삭제 동작. — ✅
10. 저장검색 CRUD 동작. — ✅
11. 데이터 품질 요약 API 동작. — ✅
12. pytest 통과. — ✅ 31개, 테스트DB 격리 버그 수정 완료(dev DB 오염 안 함)
13. README 실행법 정리. — ✅ Docker/로컬 두 경로 + 관리자 페이지 경로 포함
14. 모든 예측/수익률/위험도 응답에 고지문 포함. — ✅
15. 개인정보 필드 마스킹 확인(`/mask-check` 통과). — ✅ `app/core/masking.py` 구현, `raw_source_records` 저장 경로에 적용, 실제 Postgres에 마스킹된 값으로 저장되는 것 확인
