# Progress Log (append-only)

> 세션 종료 시 아래 형식으로 요약을 추가한다. 과거 대화 대신 이 파일을 신뢰한다.

## 형식
- [YYYY-MM-DD] Phase N: 한 일 / 다음 할 일 / 열린 이슈

## 로그
- [2026-07-10] Phase 1~6: MVP 전체 구현 완료(서브에이전트 병렬 실행). pytest 31개 통과. GitHub 저장소(`hoininsight-commits/auction-intelligence-agent`) 생성 및 push. Docker Desktop 설치 후 `docker compose up`으로 실기동 검증 완료.
- [2026-07-10] 후순위 기능: 실제 온비드 API, 실제 국토부 실거래가 API, 관리자 웹(`/admin`) 구현 및 커밋/푸시 완료. ML모델/푸시알림/결제/모바일앱은 스코프 미정으로 스킵 결정.
- [2026-07-10] 버그 수정: pytest가 `conftest.py`의 `setdefault` 때문에 Docker 환경에서 dev DB(`auction_db`)를 DROP/TRUNCATE하던 문제 발견 및 수정 — `DATABASE_URL`을 항상 `TEST_DATABASE_URL`로 강제 override하도록 변경.
- [2026-07-10] Claude Code 설정 세트(`.claude/memory`, `.claude/commands`, `.claude/agents`) 도입, CLAUDE.md를 진입점 형태로 슬림화.
- [2026-07-10] 개인정보 마스킹 구현: `app/core/masking.py`(전화번호/주민등록번호/차량번호/라벨링된 이름 정규식 마스킹), `raw_source_repository.py`에 적용, 실 Postgres에 마스킹된 값으로 저장되는 것 확인. ruff 도입 및 미사용 import 6건 자동 정리(pytest 37개 전체 통과 유지). 남은 이슈: 모델 파일 4곳의 SQLAlchemy 문자열 forward-ref에 대한 ruff F821 10건(런타임 정상 동작, `TYPE_CHECKING` 가드 미비로 인한 lint 오탐 — 다음 세션 후보).
- [2026-07-11] 국토부 커넥터 법정동코드 매핑(`real_transaction_connector.py`의 `_LAWD_CD_MAP`) 확장: 기존 9개 시군구 → 전국 17개 시도 250개 시/군/구 전체(2023년 대구 군위군 편입 등 최신 개편 반영, 출처 code.go.kr). 세종특별자치시처럼 구/군 구분 없는 지역을 위해 `_resolve_lawd_cd`에 sido 단독 매핑 조회 분기 추가, 에러 메시지가 250개 전체를 나열하지 않도록 개수 요약으로 축약. 이 세션(집)엔 docker/pytest/ruff가 설치돼 있지 않아 `/run-checks` 미실행 — 문법 검증(ast.parse)과 매핑 중복 키/코드 검사만 통과 확인. 다음 세션에서 Docker 환경으로 `/run-checks` 재검증 필요.
