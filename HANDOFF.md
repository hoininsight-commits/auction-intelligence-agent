# HANDOFF

> 세션을 새로 시작할 때 이 파일을 먼저 읽는다. 상세 규칙/아키텍처는 `CLAUDE.md`와 `.claude/memory/*.md`를 참조.

## 마지막 업데이트
2026-07-10 — 이 Mac(`imtaehun-ui-MacBookPro`)에서 MVP 전체 구현 + 후순위 기능 일부 + Docker 실기동 검증까지 완료한 상태.
2026-07-11 — 집 Mac(Mac mini, M4)에 Homebrew+Docker Desktop 신규 설치, `/run-checks` 전체 재검증 완료 (아래 참고).

## 지금 상태 (한눈에)
- **저장소**: https://github.com/hoininsight-commits/auction-intelligence-agent (public)
- **최신 커밋**: `900d3e2` "ruff format . 일괄 적용 (75개 파일 스타일 통일)"
- **working tree**: clean (미커밋 변경 없음)
- **pytest**: 37/37 통과 (집 Mac, Docker 신규 설치 환경에서 재검증 완료)
- **ruff check(lint) / ruff format --check**: 둘 다 통과 (F821 0건, 스타일 드리프트 해소)
- **Docker**: 집 Mac(Mac mini, M4)에 Homebrew+Docker Desktop 신규 설치 후 `docker compose up -d --build` 정상 기동 검증 완료 (app/postgres/redis 3개 컨테이너)
- **테스트 DB**: `auction_test_db`는 `docker compose up`만으로는 생성되지 않음 — 최초 1회 `docker compose exec postgres psql -U auction -d auction_db -c "CREATE DATABASE auction_test_db;"` 필요 (README에 안내 추가)

## 완료된 작업
1. **MVP Phase 1~6** (지시서 `docs/개발지시서-v1.0.md` 기준) — 전부 완료
   - FastAPI 골격, DB 13개 테이블 + Alembic, 검색/상세/관심물건/저장검색/수익률 API, rule-v1 룰 기반 예측, 데이터품질/관리자 API, Mock 수집 Connector + pipeline, pytest, README
2. **실제 온비드 Open API 연동** (`app/ingestion/onbid_connector.py`) — `getKamcoPbctCltrList`, `ONBID_API_KEY` 필요 (미보유, 실호출 미검증 — 파싱/정규화 로직은 목업 XML로 단위 검증됨)
3. **실제 국토부 실거래가 API 연동** (`app/ingestion/real_transaction_connector.py`) — `getRTMSDataSvcAptTradeDev`, `MOLIT_API_KEY` + 법정동코드(LAWD_CD, 9개 시군구만 하드코딩 매핑) 필요
4. **관리자 웹** (`app/static/admin/index.html`, `/admin`) — 데이터품질 요약 + 경매물건 검색/필터/상세 모달, 빌드 스텝 없는 정적 페이지
5. **Claude Code 프로젝트 설정 세트** — `.claude/memory/*`, `.claude/commands/*` (`/run-checks`, `/new-connector`, `/add-endpoint`, `/db-migrate`, `/mask-check`), `.claude/agents/*` (price-prediction/data-quality/risk-analysis)
6. **개인정보 마스킹** (`app/core/masking.py`) — 전화번호/주민등록번호/차량번호판/라벨링된 이름 정규식 마스킹, `raw_source_records` 저장 경로에 적용, 실 Postgres에 마스킹된 값으로 저장되는 것 검증됨
7. **버그 수정**: `tests/conftest.py`가 `setdefault`를 써서 Docker 환경에서 dev DB(`auction_db`)를 pytest가 DROP/TRUNCATE하던 문제 — `TEST_DATABASE_URL`로 강제 override하도록 수정
8. ruff 도입 + 미사용 import 6건 자동 정리

## 스킵하기로 결정한 것 (사용자 확인됨, 재논의 없이 그대로 두면 됨)
- ML 모델 — 실 낙찰 데이터가 seed mock 수준뿐이라 학습 무의미하다고 판단, 보류
- 푸시 알림 실연동 — 받을 클라이언트(모바일/프론트) 없어서 보류
- 결제 기능 — 요금제 미정으로 보류
- 모바일 앱 — 보류
- 법원 경매 크롤링 — **영구 금지** (지시서 원칙, 법적 리스크)

## 알려진 이슈 / 다음 세션 후보
1. **온비드/국토부 API 실호출 미검증** — 실제 서비스키(`ONBID_API_KEY`, `MOLIT_API_KEY`)가 없어서 파싱 로직만 목업으로 검증됨. data.go.kr에서 키 발급 후 실제 호출 테스트 필요. 발급 경로는 `.env.example`의 해당 키 주석 참고.
2. ~~국토부 커넥터 법정동코드 매핑이 9개 시군구만 하드코딩됨~~ → 2026-07-11 전국 250개 시/군/구로 확장 완료 (`real_transaction_connector.py`의 `_LAWD_CD_MAP`). 세종시 등 구/군 없는 지역은 sido 단독 매핑으로 처리. **`/run-checks`로 재검증 완료** (아래 참고).
3. ~~ruff F821 10건 미해결~~ → 2026-07-11 해소: `app/models/{auction_item,auction_result,real_estate_detail,vehicle_detail,price_prediction,risk_assessment}.py` 6개 파일에 `TYPE_CHECKING` 가드 import 추가 (순환 import 없음, 런타임 동작 영향 없음). **`ruff check` 0건 확인 완료** (아래 참고).
4. **cron/스케줄러 미연결** — `app/workers/celery_app.py`, `app/ingestion/scheduler.py` 구조는 있지만 실제 주기 실행(Celery Beat 등)은 안 붙어있음. 데이터 수집은 수동 트리거만 가능.
5. ~~`ruff format --check` 전체 미통과 (75개 파일)~~ → 2026-07-11 `ruff format .` 일괄 적용으로 해소. 로직 변경 없음, `ruff check`/pytest 37/37 재확인 완료.
6. **§7.7 수익률 API 지시서 예시 오류** — 지시서의 `safety_margin` 예시값(42,000,000)이 지시서 자신의 공식과 안 맞음(공식대로면 7,750,000). 코드는 공식 기준으로 구현 — 이게 맞는 것으로 최종 결정됨, 재논의 불필요.

## 집에서 이어서 시작하는 법
```bash
# 1) 전역 Claude Code 설정 복원 (~/claude-config.tar.gz를 이 세션에서 전달받았다면)
tar xzf claude-config.tar.gz -C ~/

# 2) 저장소 clone (~/claude/ 아래에 두면 auto-memory 경로와 일치)
mkdir -p ~/claude
git clone https://github.com/hoininsight-commits/auction-intelligence-agent.git ~/claude/auction-intelligence-agent
cd ~/claude/auction-intelligence-agent

# 3) 실행
cp .env.example .env
docker compose up -d --build
docker compose exec app alembic upgrade head
docker compose exec app python -m app.seed.seed_sample_data
# http://localhost:8000/docs, http://localhost:8000/admin
```
Docker Desktop이 없다면 먼저 설치: `brew install --cask docker` (sudo 암호는 Mac 로그인 암호, 터미널에 입력해도 화면엔 아무것도 안 보이는 게 정상).

## 세션 시작 시 체크리스트
1. 이 파일(`HANDOFF.md`) 읽기
2. `git log --oneline -5`로 최신 커밋 확인, `git status`로 미커밋 변경 확인
3. `.claude/memory/progress.md`에서 최근 로그 확인
4. `.claude/memory/roadmap.md`에서 후순위 기능 진행 상태 확인
5. 기능 작업 끝나면 커밋 + `git push` + `.claude/memory/progress.md`에 로그 추가 + 이 파일 갱신
