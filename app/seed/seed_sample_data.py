"""샘플 데이터 시드 스크립트 (지시서 §12).

실행:
    python -m app.seed.seed_sample_data

포함 데이터 (지시서 §12):
1. 테스트 사용자 1명 (id=1, test@example.com, 테스트사용자)
2. 서울 아파트 경매 샘플 3건
3. 경기 빌라 경매 샘플 2건
4. 부산 상가 공매 샘플 1건
5. 차량 공매 샘플 1건
6. 실거래가 샘플 10건
7. 낙찰 결과 샘플 10건
8. 위험도 샘플 3건
9. 예측 결과 샘플 3건
"""

import asyncio
from datetime import date, datetime, timedelta, timezone

from sqlalchemy import select

from app.core.constants import TEST_USER_EMAIL, TEST_USER_ID, TEST_USER_NICKNAME
from app.core.database import AsyncSessionLocal, engine
from app.core.disclaimers import PREDICTION_DISCLAIMER, RISK_ANALYSIS_DISCLAIMER
from app.models import (
    AuctionItem,
    AuctionResult,
    Base,
    PricePrediction,
    PropertyTransaction,
    RealEstateDetail,
    RiskAssessment,
    User,
    VehicleDetail,
)


async def seed() -> None:
    async with engine.begin() as conn:
        # 개발 편의를 위해 테이블이 없으면 생성한다 (실제 배포는 alembic migration 사용).
        await conn.run_sync(Base.metadata.create_all)

    async with AsyncSessionLocal() as session:
        existing_user = await session.scalar(select(User).where(User.id == TEST_USER_ID))
        if existing_user is not None:
            print("Seed 데이터가 이미 존재합니다. 스킵합니다.")
            return

        # 1. 테스트 사용자
        user = User(
            id=TEST_USER_ID,
            email=TEST_USER_EMAIL,
            nickname=TEST_USER_NICKNAME,
            is_active=True,
            is_admin=False,
        )
        session.add(user)
        await session.flush()

        # 2. 서울 아파트 경매 3건
        seoul_apartments = [
            AuctionItem(
                source="court",
                source_item_id="2024TAGYUNG0001",
                auction_type="real_estate",
                case_number="2024타경1001",
                item_number="1",
                category="apartment",
                sub_category=None,
                title="서울 강남구 대치동 은마아파트 101동 1503호",
                address="서울특별시 강남구 대치동 316",
                sido="서울특별시",
                sigungu="강남구",
                eupmyeondong="대치동",
                latitude=37.4980,
                longitude=127.0632,
                appraisal_price=2_200_000_000,
                minimum_price=1_408_000_000,
                deposit_price=140_800_000,
                bid_date=datetime.now(timezone.utc).replace(tzinfo=None) + timedelta(days=14),
                bid_location="서울중앙지방법원 경매법정",
                fail_count=2,
                status="active",
            ),
            AuctionItem(
                source="court",
                source_item_id="2024TAGYUNG0002",
                auction_type="real_estate",
                case_number="2024타경1002",
                item_number="1",
                category="apartment",
                sub_category=None,
                title="서울 마포구 상암동 월드컵파크 3단지 401호",
                address="서울특별시 마포구 상암동 1595",
                sido="서울특별시",
                sigungu="마포구",
                eupmyeondong="상암동",
                latitude=37.5794,
                longitude=126.8912,
                appraisal_price=1_100_000_000,
                minimum_price=880_000_000,
                deposit_price=88_000_000,
                bid_date=datetime.now(timezone.utc).replace(tzinfo=None) + timedelta(days=21),
                bid_location="서울서부지방법원 경매법정",
                fail_count=1,
                status="active",
            ),
            AuctionItem(
                source="court",
                source_item_id="2024TAGYUNG0003",
                auction_type="real_estate",
                case_number="2024타경1003",
                item_number="2",
                category="apartment",
                sub_category=None,
                title="서울 노원구 상계동 주공아파트 12동 802호",
                address="서울특별시 노원구 상계동 720",
                sido="서울특별시",
                sigungu="노원구",
                eupmyeondong="상계동",
                latitude=37.6598,
                longitude=127.0736,
                appraisal_price=520_000_000,
                minimum_price=332_800_000,
                deposit_price=33_280_000,
                bid_date=datetime.now(timezone.utc).replace(tzinfo=None) + timedelta(days=10),
                bid_location="서울북부지방법원 경매법정",
                fail_count=2,
                status="active",
            ),
        ]

        # 3. 경기 빌라 경매 2건
        gyeonggi_villas = [
            AuctionItem(
                source="court",
                source_item_id="2024TAGYUNG0004",
                auction_type="real_estate",
                case_number="2024타경2001",
                item_number="1",
                category="villa",
                sub_category=None,
                title="경기 수원시 팔달구 매교동 다세대주택 2층 202호",
                address="경기도 수원시 팔달구 매교동 45-3",
                sido="경기도",
                sigungu="수원시 팔달구",
                eupmyeondong="매교동",
                latitude=37.2775,
                longitude=127.0176,
                appraisal_price=280_000_000,
                minimum_price=196_000_000,
                deposit_price=19_600_000,
                bid_date=datetime.now(timezone.utc).replace(tzinfo=None) + timedelta(days=18),
                bid_location="수원지방법원 경매법정",
                fail_count=1,
                status="active",
            ),
            AuctionItem(
                source="court",
                source_item_id="2024TAGYUNG0005",
                auction_type="real_estate",
                case_number="2024타경2002",
                item_number="1",
                category="villa",
                sub_category=None,
                title="경기 부천시 원미구 중동 연립주택 3층 301호",
                address="경기도 부천시 원미구 중동 1123",
                sido="경기도",
                sigungu="부천시 원미구",
                eupmyeondong="중동",
                latitude=37.5049,
                longitude=126.7648,
                appraisal_price=230_000_000,
                minimum_price=184_000_000,
                deposit_price=18_400_000,
                bid_date=datetime.now(timezone.utc).replace(tzinfo=None) + timedelta(days=25),
                bid_location="인천지방법원 부천지원 경매법정",
                fail_count=0,
                status="scheduled",
            ),
        ]

        # 4. 부산 상가 공매 1건
        busan_commercial = AuctionItem(
            source="onbid",
            source_item_id="2024ONBID0001",
            auction_type="public_sale",
            case_number="2024-공매-3001",
            item_number="1",
            category="commercial",
            sub_category=None,
            title="부산 해운대구 우동 상가 1층 101호",
            address="부산광역시 해운대구 우동 1467",
            sido="부산광역시",
            sigungu="해운대구",
            eupmyeondong="우동",
            latitude=35.1631,
            longitude=129.1636,
            appraisal_price=650_000_000,
            minimum_price=455_000_000,
            deposit_price=45_500_000,
            bid_date=datetime.now(timezone.utc).replace(tzinfo=None) + timedelta(days=12),
            bid_location="온비드 전자입찰",
            fail_count=2,
            status="active",
        )

        # 5. 차량 공매 1건
        vehicle_item = AuctionItem(
            source="onbid",
            source_item_id="2024ONBID0002",
            auction_type="vehicle",
            case_number="2024-공매-3002",
            item_number="1",
            category="vehicle",
            sub_category=None,
            title="현대 그랜저 IG 2019년식",
            address="서울특별시 강동구 성내동 보관소",
            sido="서울특별시",
            sigungu="강동구",
            eupmyeondong="성내동",
            latitude=37.5301,
            longitude=127.1238,
            appraisal_price=18_000_000,
            minimum_price=12_600_000,
            deposit_price=1_260_000,
            bid_date=datetime.now(timezone.utc).replace(tzinfo=None) + timedelta(days=8),
            bid_location="온비드 전자입찰",
            fail_count=1,
            status="active",
        )

        all_items = [*seoul_apartments, *gyeonggi_villas, busan_commercial, vehicle_item]
        session.add_all(all_items)
        await session.flush()

        # 부동산 상세 (아파트 3 + 빌라 2 + 상가 1 = 6건)
        real_estate_items = [*seoul_apartments, *gyeonggi_villas, busan_commercial]
        for idx, item in enumerate(real_estate_items):
            session.add(
                RealEstateDetail(
                    auction_item_id=item.id,
                    building_area=84.5 + idx,
                    land_area=45.2 + idx,
                    exclusive_area=59.8 + idx,
                    floor_info=f"{3 + idx}층/{15 + idx}층",
                    approval_date=date(2005 + idx, 6, 1),
                    land_rights="대지권 있음",
                    building_structure="철근콘크리트구조",
                    usage_type="공동주택" if item.category != "commercial" else "근린생활시설",
                    appraisal_summary="감정평가서 요약 (샘플 데이터)",
                    occupancy_summary="점유관계 조사 요약 (샘플 데이터)",
                    tenant_summary="임차인 없음 (샘플 데이터)",
                    registry_summary="등기부 요약 (샘플 데이터)",
                    document_summary="매각물건명세서 요약 (샘플 데이터)",
                )
            )

        # 차량 상세 1건
        session.add(
            VehicleDetail(
                auction_item_id=vehicle_item.id,
                manufacturer="현대",
                model="그랜저 IG",
                trim="3.0 캘리그래피",
                model_year=2019,
                mileage=68_000,
                fuel_type="가솔린",
                transmission="자동",
                color="펄화이트",
                accident_history="단순 교환 이력 있음 (샘플 데이터)",
                inspection_summary="검사 결과 양호 (샘플 데이터)",
                storage_location="서울 강동구 보관소",
            )
        )

        # 6. 실거래가 샘플 10건
        property_transactions = (
            [
                PropertyTransaction(
                    property_type="apartment",
                    address="서울특별시 강남구 대치동 316",
                    sido="서울특별시",
                    sigungu="강남구",
                    eupmyeondong="대치동",
                    complex_name="은마아파트",
                    exclusive_area=84.43,
                    deal_price=2_350_000_000 - i * 20_000_000,
                    deal_year=2024,
                    deal_month=(i % 12) + 1,
                    deal_day=(i % 27) + 1,
                    floor_info=f"{5 + i}",
                    build_year=1979,
                    source="molit",
                )
                for i in range(4)
            ]
            + [
                PropertyTransaction(
                    property_type="apartment",
                    address="서울특별시 마포구 상암동 1595",
                    sido="서울특별시",
                    sigungu="마포구",
                    eupmyeondong="상암동",
                    complex_name="월드컵파크 3단지",
                    exclusive_area=59.96,
                    deal_price=1_150_000_000 - i * 15_000_000,
                    deal_year=2024,
                    deal_month=(i % 12) + 1,
                    deal_day=(i % 27) + 1,
                    floor_info=f"{3 + i}",
                    build_year=2002,
                    source="molit",
                )
                for i in range(3)
            ]
            + [
                PropertyTransaction(
                    property_type="villa",
                    address="경기도 수원시 팔달구 매교동 45-3",
                    sido="경기도",
                    sigungu="수원시 팔달구",
                    eupmyeondong="매교동",
                    complex_name=None,
                    exclusive_area=45.2,
                    deal_price=295_000_000 - i * 5_000_000,
                    deal_year=2024,
                    deal_month=(i % 12) + 1,
                    deal_day=(i % 27) + 1,
                    floor_info=f"{2 + i}",
                    build_year=2010,
                    source="molit",
                )
                for i in range(3)
            ]
        )
        session.add_all(property_transactions)

        # 7. 낙찰 결과 샘플 10건 (샘플 물건 6건에 순환 배정)
        result_statuses = ["sold", "failed"]
        auction_results = []
        for i in range(10):
            item = real_estate_items[i % len(real_estate_items)]
            status = result_statuses[0] if i % 3 != 0 else result_statuses[1]
            winning_rate = 78.5 + (i % 5) * 2.1
            auction_results.append(
                AuctionResult(
                    auction_item_id=item.id,
                    result_status=status,
                    winning_price=int(item.minimum_price * (winning_rate / 100))
                    if item.minimum_price
                    else None,
                    winning_rate=winning_rate,
                    bidder_count=1 + (i % 6),
                    result_date=date(2024, ((i % 12) + 1), (i % 27) + 1),
                )
            )
        session.add_all(auction_results)

        # 8. 위험도 샘플 3건
        risk_targets = seoul_apartments[:2] + [busan_commercial]
        risk_levels = ["low", "medium", "high"]
        risk_assessments = [
            RiskAssessment(
                auction_item_id=risk_targets[i].id,
                risk_level=risk_levels[i],
                legal_risk_score=[10.0, 45.0, 75.0][i],
                occupancy_risk_score=[5.0, 30.0, 60.0][i],
                asset_risk_score=[15.0, 25.0, 55.0][i],
                risk_factors={
                    "factors": [
                        "말소기준권리 확인 필요",
                        "임차인 대항력 여부 확인 필요",
                    ][: i + 1]
                },
                disclaimer=RISK_ANALYSIS_DISCLAIMER,
            )
            for i in range(3)
        ]
        session.add_all(risk_assessments)

        # 9. 예측 결과 샘플 3건
        prediction_targets = seoul_apartments[:2] + [busan_commercial]
        confidences = ["high", "medium", "low"]
        price_predictions = []
        for i, item in enumerate(prediction_targets):
            base = item.minimum_price or 0
            mid_rate = 82.0 + i * 3
            spread = 3.0 if confidences[i] == "high" else 6.0
            price_predictions.append(
                PricePrediction(
                    auction_item_id=item.id,
                    predicted_price_low=int(base * (mid_rate - spread) / 100),
                    predicted_price_mid=int(base * mid_rate / 100),
                    predicted_price_high=int(base * (mid_rate + spread) / 100),
                    predicted_rate_low=mid_rate - spread,
                    predicted_rate_mid=mid_rate,
                    predicted_rate_high=mid_rate + spread,
                    confidence=confidences[i],
                    model_version="rule-v1",
                    explanation={
                        "base": "similar_case_average",
                        "adjustment_factors": {
                            "fail_count_factor": 1.0,
                            "legal_risk_factor": 1.0,
                            "regional_demand_factor": 1.0,
                            "price_gap_factor": 1.0,
                        },
                    },
                    disclaimer=PREDICTION_DISCLAIMER,
                )
            )
        session.add_all(price_predictions)

        await session.commit()
        print("Seed 데이터 삽입 완료.")


async def main() -> None:
    await seed()
    await engine.dispose()


if __name__ == "__main__":
    asyncio.run(main())
