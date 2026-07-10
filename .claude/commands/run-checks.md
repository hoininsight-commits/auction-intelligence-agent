# /run-checks

프로젝트 검증을 순서대로 실행하고 결과를 요약한다.

실행:
1. `ruff check .` 및 `ruff format --check .`
2. `alembic upgrade head` (로컬 DB 기준)
3. `pytest -q`
4. `/docs` 라우트 존재 여부 확인

규칙:
- 실패 항목만 상세히 보여준다. 통과 항목은 한 줄 요약.
- 전체 코드 재출력 금지. 수정 필요한 파일/라인만 제시.
- 완료 후 progress.md에 결과 한 줄 append 제안.