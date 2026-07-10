# /new-connector

새 데이터 소스 Connector를 생성한다. (크롤링 금지, 공식 API 또는 Mock)

입력: source 이름 (예: onbid, molit, court)

작업:
1. app/ingestion/base.py의 BaseConnector를 상속.
2. fetch_items / fetch_detail 구현. 실제 키 없으면 Mock 반환.
3. raw_source_records 저장 로직 연결.
4. 정규화 매핑을 pipeline에 등록.
5. 해당 connector 테스트 추가.

규칙:
- 크롤링/HTML 파싱 구현 금지.
- 반환 필드는 data-model.md의 enum을 따른다.