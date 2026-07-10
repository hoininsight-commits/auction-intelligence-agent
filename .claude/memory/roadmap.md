# Roadmap (개발 순서)

## MVP Phase 1~6 — 완료
1. 골격: FastAPI, Dockerfile, docker-compose, pyproject, config, DB 연결, health API
2. DB 모델/마이그레이션: Base, 13개 모델, Alembic, seed 스크립트
3. 핵심 API: 검색, 상세, 관심물건, 저장검색, 수익률 계산
4. 예측/분석: rule-v1, 예측 API, 위험도, 데이터 품질, 관리자 품질 API
5. 데이터 수집 기반: Connector 인터페이스, Mock Onbid/RealTransaction, raw 저장, pipeline, 수집 로그
6. 테스트/문서: pytest 31개 통과, README, `.env.example`, Swagger 확인, Docker 실기동 검증

## 후순위 기능 (지시서 §1.3) — 진행 상태
- [x] 실제 온비드 API 연동 (`getKamcoPbctCltrList`)
- [x] 실제 국토부 실거래가 API 연동 (`getRTMSDataSvcAptTradeDev`)
- [x] 관리자 웹 프론트엔드 (`/admin`, 정적 HTML/JS)
- [ ] ML 모델 — 보류(실 낙찰 데이터 부족, 스킵 결정)
- [ ] 푸시 알림 실연동 — 보류(수신 클라이언트 없음, 스킵 결정)
- [ ] 결제 기능 — 보류(요금제 미정, 스킵 결정)
- [ ] 모바일 앱 — 보류(스킵 결정)
- [ ] 법원 경매 크롤링 — 영구 미구현(법적 리스크, 지시서 원칙)

## 완료 — 부가 작업
- [x] 개인정보 마스킹(`app/core/masking.py`) 구현, `raw_source_records` 저장 경로 적용, 실 DB 검증 완료
- [x] pytest 테스트DB 격리 버그 수정 (dev DB 오염 방지)
- [x] ruff 도입 + 자동 수정 가능한 미사용 import 정리 (남은 10건은 SQLAlchemy 문자열 forward-ref false positive, `TYPE_CHECKING` 가드 추가로 해소 가능 — 다음 세션 후보)

각 작업 완료 시 `/run-checks` 실행 후 `progress.md` 갱신 + git commit/push.
