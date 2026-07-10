# Auction Intelligence Agent — Claude Code 진입점

> 이 파일은 짧게 유지한다. 상세 규칙은 `.claude/memory/*.md`를 필요할 때만 읽는다.
> 원본 스펙 1차 출처는 `docs/개발지시서-v1.0.md` — 이 파일과 어긋나면 지시서를 따른다.

## 프로젝트 한 줄 정의
전국 부동산 경매·공매 통합 검색 + 룰 기반 참고 낙찰가 + 수익률 계산 MVP 백엔드(FastAPI). MVP Phase 1~6 완료, 온비드/국토부 실거래가 실제 API 연동 및 관리자 웹(`/admin`) 추가 완료.

## 절대 규칙 (항상 준수)
1. 크롤링 코드는 작성하지 않는다. 외부 데이터는 공식 API 구조만 열어두고, 키가 없으면 Mock Connector를 쓴다(`ENABLE_MOCK_CONNECTORS=true`가 기본).
2. 예상 낙찰가·수익률·권리분석·상세 응답에는 반드시 `app/core/disclaimers.py`의 법적 고지문을 포함한다.
3. 채무자·소유자·임차인 이름, 차량번호, 연락처 등 개인정보는 저장 시 `app/core/masking.py`로 마스킹한다.
4. Python 3.11+, FastAPI, SQLAlchemy 2.x(async), Pydantic v2, Alembic, PostgreSQL, Redis, pytest 사용.
5. 새 코드 후에는 `/run-checks`로 검증한다.
6. 대용량 파일 전체를 반복 출력하지 않는다. 변경된 부분만 보여준다.
7. `app/api/router.py`처럼 여러 작업이 동시에 건드릴 수 있는 공유 파일은 전체를 덮어쓰지 말고 Edit으로 필요한 줄만 추가한다.

## 실행 명령어
```bash
cp .env.example .env
docker compose up -d
docker compose exec app alembic upgrade head
docker compose exec app python -m app.seed.seed_sample_data
# http://localhost:8000/docs, http://localhost:8000/admin
```

```bash
pytest                 # 컨테이너 안에서는: docker compose exec app pytest -q
alembic revision --autogenerate -m "message"
```

## 참조 (필요할 때만 읽기)
- 스택/버전: `.claude/memory/tech-stack.md`
- 아키텍처/데이터흐름/Connector 상태: `.claude/memory/architecture.md`
- 코딩/보안/개인정보/고지 규칙: `.claude/memory/conventions.md`
- DB 스키마 요약: `.claude/memory/data-model.md`
- 개발 순서 및 후순위 기능 진행상태: `.claude/memory/roadmap.md`
- 완료 기준: `.claude/memory/definition-of-done.md`
- 진행 로그: `.claude/memory/progress.md`

## 커맨드 / 서브에이전트
- `.claude/commands/`: `/run-checks`, `/new-connector`, `/add-endpoint`, `/db-migrate`, `/mask-check`
- `.claude/agents/`: `price-prediction`, `data-quality`, `risk-analysis`

## 세션 운영
- 긴 세션은 진행 요약을 `.claude/memory/progress.md`에 append 후 이어간다.
- 기능 하나 끝날 때마다 git commit + push (원격: `hoininsight-commits/auction-intelligence-agent`).
