"""API v1 라우터 등록.

Phase 1: health 라우터만 등록한다. 아래 나머지 라우터들은 각 파일이
실제 APIRouter를 구현하는 phase(주석 참고)에서 여기에 include_router로 추가한다.

    Phase 3: auction_items, watchlist, saved_searches, profitability
    Phase 4: predictions, admin
"""
from fastapi import APIRouter

from app.api.v1 import (
    admin,
    auction_items,
    health,
    predictions,
    profitability,
    saved_searches,
    watchlist,
)
from app.core.constants import API_V1_PREFIX

api_router = APIRouter(prefix=API_V1_PREFIX)

api_router.include_router(health.router)
api_router.include_router(predictions.router)
api_router.include_router(admin.router)
api_router.include_router(auction_items.router)
api_router.include_router(watchlist.router)
api_router.include_router(saved_searches.router)
api_router.include_router(profitability.router)
