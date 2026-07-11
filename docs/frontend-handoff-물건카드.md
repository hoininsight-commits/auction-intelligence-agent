# 프론트엔드 디자인 핸드오프 — 경매 물건 카드/상세 화면

> 대상: 프론트엔드 디자이너/에이전트. 백엔드 API(FastAPI)가 내려주는 필드를 기준으로 화면을 설계할 때 참고.
> 전체 프로젝트 배경은 `CLAUDE.md` 참조. 이 문서는 "물건 목록 카드 + 물건 상세 화면" 딱 이 화면 설계에만 필요한 정보로 좁혔다.

## 서비스 한 줄 설명

전국 부동산 경매·공매 물건을 검색하고, 물건마다 **참고용** 예상 낙찰가·위험도·시세 대비 판정·관심도(조회수/찜수)를 함께 보여주는 서비스. "정답을 알려주는 서비스"가 아니라 "판단 재료를 한 화면에 모아주는 서비스"라는 톤 유지가 중요 — 그래서 법적 고지문이 API 응답에 항상 같이 온다.

## 화면에 필요한 데이터 — 지금 API에 있는 것 (구현 완료)

### 목록/검색 화면 — `GET /api/v1/auction-items`

응답의 `items[]` 배열 항목 하나:

```json
{
  "id": 1,
  "source": "onbid",
  "auction_type": "real_estate",
  "case_number": "2026타경10001",
  "category": "apartment",
  "title": "서울특별시 강남구 샘플아파트",
  "address": "서울특별시 강남구 테헤란로 123",
  "sido": "서울특별시",
  "sigungu": "강남구",
  "appraisal_price": 500000000,
  "minimum_price": 400000000,
  "fail_count": 1,
  "bid_date": "2026-08-01T10:00:00",
  "predicted_price_mid": 418000000,
  "predicted_rate_mid": 83.6,
  "risk_level": "medium",
  "verdict": "fair",
  "status": "active",
  "view_count": 128,
  "watch_count": 12
}
```

- `appraisal_price` / `minimum_price` — 감정가 / 최저입찰가 (원 단위 정수)
- `fail_count` — 유찰 횟수. 카드에서 "N회 유찰" 배지로 흔히 씀
- `predicted_price_mid` / `predicted_rate_mid` — 참고용 예상 낙찰가와 그 비율(%). **AI 정답 아님**, 룰 계산값
- `risk_level` — `"high"` / `"medium"` / `"unknown"` 셋 중 하나 (현재 `"low"`는 실제로는 거의 안 나옴 — 아래 "종합 판정" 항목 참고)
- `verdict` — `"good"` / `"fair"` / `"caution"` / `null`. 아래 "종합 판정 배지" 항목 참고
- `status` — `active` / `scheduled` / `sold` / `failed` / `cancelled` / `expired` / `unknown`
- `view_count` / `watch_count` — 조회수 / 찜수. 아래 "관심도" 항목 참고

### 상세 화면 — `GET /api/v1/auction-items/{id}`

목록 필드 + 아래가 추가:

```json
{
  "view_count": 129,
  "watch_count": 12,
  "real_estate_detail": { "exclusive_area": 84.5, "floor_info": "12층", "usage_type": "공동주택" },
  "latest_prediction": {
    "predicted_price_low": 405000000,
    "predicted_price_mid": 418000000,
    "predicted_price_high": 432000000,
    "predicted_rate_low": 81.0,
    "predicted_rate_mid": 83.6,
    "predicted_rate_high": 86.4,
    "confidence": "medium",
    "model_version": "rule-v1",
    "verdict": "fair"
  },
  "risk_assessment": {
    "risk_level": "medium",
    "risk_factors": ["점유자 확인 필요", "매각물건명세서 확인 필요"]
  },
  "nearby_transactions": [ { "complex_name": "샘플아파트", "deal_price": 470000000, "deal_year": 2026, "deal_month": 6 } ],
  "disclaimer": "본 서비스의 예상 낙찰가, 수익률, 권리분석, 위험도 정보는 참고용입니다. 실제 입찰 및 투자 결정은 사용자의 책임이며, 입찰 전 법무사, 변호사, 세무사 등 전문가 검토를 권장합니다. 본 서비스는 낙찰 결과나 투자 수익을 보장하지 않습니다."
}
```

- `latest_prediction.confidence` — `"high"` / `"medium"` / `"low"`. 예측 범위(low~high 폭)와 함께 "이 예측이 얼마나 믿을 만한가"를 화면에 표현할 때 씀. confidence가 낮으면 범위가 넓어짐 — 슬라이더/범위 바 UI에서 폭 차이로 시각화 가능
- `nearby_transactions` — 인근 실거래가 비교용. 빈 배열일 수 있음(데이터 없는 지역)
- **`disclaimer` 문구는 화면에서 임의로 줄이거나 빼면 안 됨** — 법적 요구사항, 절대 규칙

## 관심도·종합판정 — 구현 완료 (2026-07-11)

목록/상세 API 둘 다에 아래 필드가 이제 실제로 채워져서 내려온다.

### 1. 관심도 — `view_count`, `watch_count`

- 의미: 이 물건을 몇 명이 봤는지(view_count), 몇 명이 찜했는지(watch_count)
- 상세 조회할 때마다 view_count +1, 관심물건 추가/삭제할 때 watch_count ±1
- **"인기 물건" 뱃지 같은 임계값 기반 UI는 아직 넣지 말 것** — 실사용 트래픽이 없어서 몇 회 이상을 "인기"로 볼지 기준이 없음. 우선 숫자 그대로 노출하는 디자인으로 잡아달라 (예: "조회 128 · 찜 12")

### 2. 종합 판정 배지 — `verdict`

목록 항목(`AuctionItemSearchItem`)과 상세의 `latest_prediction.verdict`에 문자열로 내려온다. **값은 영문 코드**이고, 화면 라벨은 아래처럼 매핑해서 쓰면 됨:

| API 값(`verdict`) | 화면 라벨(제안) | 의미 |
|---|---|---|
| `"good"` | 우수 | 시세보다 감정가가 쌈(시세괴리율 0.90 이하) **그리고** 위험도 낮음 |
| `"fair"` | 보통 | 위 두 조건에 해당 안 되는 나머지 전부(정보 부족 포함) |
| `"caution"` | 주의 | 위험도 높음, 또는 시세보다 감정가가 20% 넘게 비쌈 |
| `null` | (배지 숨김) | 아직 예측이 계산/저장되지 않은 물건 — `predict-price` API가 최소 1번 호출된 물건만 값이 생김 |

- 새 AI 판단이 아니라 이미 있던 rule-v1 예측 계산 안의 "시세괴리율"과 위험도를 조합한 룰 하나. 예측 자체가 없으면(=`predicted_price_mid`도 `null`) verdict도 `null` — 이 둘은 항상 같이 비거나 같이 참
- 실제 데이터에서는 `risk_level`이 `"low"`로 저장된 물건이 드물어서(기본값은 "정보부족=unknown"으로 보수적으로 잡음) `"good"`이 자주 안 뜰 수 있음 — 버그 아니라 "증거 없으면 우수라고 안 한다"는 의도된 보수적 설계
- 디자인 관점에서 3가지 상태만 있으면 됨: `우수`(긍정색), `보통`(중립색), `주의`(경고색) — 이미 `risk_level`에 medium/high/unknown 쓰던 것과 톤을 맞추면 됨
- 이 배지는 감정/판단을 대신하는 게 아니라 "먼저 볼 것"을 골라주는 용도라는 뉘앙스가 중요 — 옆에 작은 느낌표 아이콘 + disclaimer 툴팁 정도로 "참고용" 신호를 같이 주는 걸 권장

## 디자인 톤 참고

- 색상: 경매/법원/공적 데이터라는 소재라 과도하게 화려한 톤보다는 신뢰감 있는 톤 권장. 위험도·판정 배지에 신호등식 색(초록/노랑/빨강)을 그대로 쓰기보다는, 절제된 팔레트 안에서 상태만 구분되게 하는 것을 추천 (전면 리서치 아티팩트에서 사용한 브라스/잉크 톤 참고 가능하나 강제 아님)
- 숫자가 많은 화면(가격, %, 조회수)이라 표/카드 내 숫자는 자릿수 정렬(tabular figures) 신경 써줄 것
- `disclaimer` 문구는 상세 화면 최소 1곳에 항상 노출 — 위치는 디자인 재량이나 생략 불가
