# HANDOFF

> 세션을 새로 시작할 때 이 파일을 먼저 읽는다. 상세 규칙/아키텍처는 `CLAUDE.md`와 `.claude/memory/*.md`를 참조.

## 마지막 업데이트
2026-07-10 — 이 Mac(`imtaehun-ui-MacBookPro`)에서 MVP 전체 구현 + 후순위 기능 일부 + Docker 실기동 검증까지 완료한 상태.
2026-07-11 — 집 Mac(Mac mini, M4)에 Homebrew+Docker Desktop 신규 설치, `/run-checks` 전체 재검증. 온비드/국토부 실거래가 API 실제 서비스키로 실호출 검증 + 온비드 커넥터 전면 재작성. 실제 데이터 수집 파이프라인(`ENABLE_MOCK_CONNECTORS=false`) end-to-end 검증. cron/스케줄러(Celery Beat) 실제 연결 + 국토부 전국 순회 구현까지 완료 — **알려진 이슈 항목이 사실상 전부 해소된 상태** (아래 참고).

## 지금 상태 (한눈에)
- **저장소**: https://github.com/hoininsight-commits/auction-intelligence-agent (public)
- **최신 커밋**: (아래 커밋 예정) "cron/스케줄러 실제 연결 + 국토부 실거래가 전국 순회 구현"
- **working tree**: 커밋 대기 중 (celery_app.py/tasks.py/scheduler.py/docker-compose.yml/real_transaction_connector.py + 문서)
- **pytest**: 37/37 통과. **ruff check/format**: 둘 다 통과
- **Docker**: 집 Mac(Mac mini, M4)에 Homebrew+Docker Desktop 신규 설치, `docker compose up -d --build` 정상 기동 검증 완료. `worker`/`beat` 서비스도 추가되어 함께 기동됨.
- **테스트 DB**: `auction_test_db`는 `docker compose up`만으로는 생성되지 않음 — 최초 1회 `docker compose exec postgres psql -U auction -d auction_db -c "CREATE DATABASE auction_test_db;"` 필요 (README에 안내 추가)
- **실제 API 키**: `.env`에 `ONBID_API_KEY`/`MOLIT_API_KEY` 실제 서비스키 반영됨(gitignore 처리, 저장소엔 안 올라감). **`ENABLE_MOCK_CONNECTORS=false`로 변경되어 있음** — 이 Mac의 `.env`는 이제 실제 온비드/국토부 API를 호출한다(beat이 매시간/매일 자동 호출도 함). 다른 환경에서 Mock을 쓰려면 `.env`에서 다시 `true`로 바꿀 것.
- **주의**: `check/` 디렉터리에 data.go.kr 활용신청 화면 캡처와 서비스키가 그대로 담긴 스크린샷/문서가 있음 — `.gitignore`에 등록되어 커밋되지 않지만, 다른 사람과 공유 시 주의

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
1. ~~온비드/국토부 API 실호출 미검증~~ → 2026-07-11 실제 서비스키로 검증 완료.
   - **국토부 실거래가**: 기존 구현 그대로 정상 동작. Base URL을 http → https로 수정.
   - **온비드**: 기존 코드가 참조하던 데이터셋(`data.go.kr/data/15000851`, 오퍼레이션 `getKamcoPbctCltrList`)이 **폐기**되어 404. 실제로는 "차세대 온비드" API 2종으로 이전됨 — `app/ingestion/onbid_connector.py`를 전면 재작성:
     - 물건목록: `https://apis.data.go.kr/B010003/OnbidRlstListSrvc2/getRlstCltrList2` (필수 파라미터 `prptDivCd`, `pvctTrgtYn`)
     - 물건상세: `https://apis.data.go.kr/B010003/OnbidCltrBidDtlSrvc2/getCltrBidInf2` (필수 파라미터 `cltrMngNo`, `pbctCdtnNo`, 물건목록 응답에서 얻음)
     - `source_item_id` 형식이 `{cltrMngNo}::{pbctCdtnNo}`로 변경됨 (cltrMngNo 자체에 하이픈이 있어 `-` 대신 `::` 구분자 사용)
     - 물건상세 오퍼레이션은 소재지/감정가/용도 필드를 내려주지 않음 — 목록 조회 결과와 병합 필요(현재는 목록 필드만으로 정규화, 상세는 입찰 조건 위주)
   - 실제 호출로 국토부/온비드 둘 다 정상 응답 확인. `.env.example`/`.env`에 실제 서비스키 반영, `/run-checks` 재검증 완료 (ruff/format/pytest 37/37 통과)
   - 이어서 `ENABLE_MOCK_CONNECTORS=false`로 바꾸고 **실제 파이프라인**(`collect_source_items` → raw 저장 → 정규화 upsert → `collection_jobs` 로그)까지 end-to-end 검증. 온비드는 파라미터 없이도 성공(100건 수집/삽입)했지만, 국토부는 `LAWD_CD`가 필수라 `collect_source_items(source)`가 파라미터 없이 호출하는 기존 구조에서는 실패했음(앱 크래시 없이 `collection_jobs.status="failed"`로 안전하게 기록되긴 함).
   - 이 문제를 해결하기 위해 `collect_source_items(source, **connector_kwargs)`로 확장해 `connector.fetch_items(**connector_kwargs)`에 그대로 전달하도록 변경. `app/workers/tasks.py`의 Celery task와 `app/ingestion/scheduler.py`의 `ScheduledJob`에도 `default_kwargs` 필드를 추가해 관통시킴. `ScheduledJob`의 `real_transaction` 항목은 예시로 서울 종로구를 기본값으로 채워둠(전국 250개 시/군/구를 순회하는 로직은 아직 없음 — 필요하면 후속 작업으로 `_LAWD_CD_MAP` 전체를 반복하는 로직 추가).
   - 재검증: 온비드(100건), 국토부(서울 종로구, 20건→19신규+1갱신) 둘 다 실제 파이프라인으로 성공. 재실행 시 upsert 멱등성도 확인(같은 데이터 재수집 시 `updated_count`로 정상 집계). `/run-checks` 최종 재확인(ruff/format/pytest 37/37) 통과.
2. ~~국토부 커넥터 법정동코드 매핑이 9개 시군구만 하드코딩됨~~ → 2026-07-11 전국 250개 시/군/구로 확장 완료 (`real_transaction_connector.py`의 `_LAWD_CD_MAP`). 세종시 등 구/군 없는 지역은 sido 단독 매핑으로 처리. **`/run-checks`로 재검증 완료** (아래 참고).
3. ~~ruff F821 10건 미해결~~ → 2026-07-11 해소: `app/models/{auction_item,auction_result,real_estate_detail,vehicle_detail,price_prediction,risk_assessment}.py` 6개 파일에 `TYPE_CHECKING` 가드 import 추가 (순환 import 없음, 런타임 동작 영향 없음). **`ruff check` 0건 확인 완료** (아래 참고).
4. ~~cron/스케줄러 미연결~~ → 2026-07-11 연결 완료: `app/workers/celery_app.py`에 `beat_schedule` 추가(온비드 매시간 `collect_source_items_task`, 국토부 실거래가 전국 순회 매일 새벽 3시 KST `collect_real_transaction_all_regions_task`). 국토부 전국 순회는 새 `real_transaction_connector.get_supported_regions()`으로 `_LAWD_CD_MAP` 250개 시/군/구 전체를 반복하며 지역별로 별도 `collect_source_items` 호출 + `collection_jobs` 로그를 남긴다(세종처럼 구/군 없는 지역도 처리). `docker-compose.yml`에 `worker`/`beat` 서비스 추가해 `docker compose up -d`로 함께 기동됨. 태스크 큐잉(`.delay()`)→워커 실행→결과 반환 전체 경로와 3개 지역(종로구/중구/세종) 실호출을 직접 검증. **beat의 실제 매시간/매일 트리거는 몇 시간~하루를 기다려야 확인 가능** — 아직 그 시점까지 관찰하지는 못했으니 다음 세션에서 `docker compose logs beat`로 실제 스케줄 발화 여부 확인 권장.
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
