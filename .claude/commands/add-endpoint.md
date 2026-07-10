# /add-endpoint

새 API 엔드포인트를 추가한다.

입력: 메서드 + 경로 + 목적

작업:
1. schemas에 요청/응답 Pydantic 모델 정의.
2. api/v1에 라우터 추가 (검증+서비스 호출만).
3. services에 비즈니스 로직 구현.
4. repositories에 DB 접근 추가.
5. pytest 추가.
6. 투자/예측/수익률/위험 관련이면 고지문 포함 확인.

규칙:
- 라우터에 비즈니스 로직 넣지 않는다.
- /api/v1 prefix 유지.