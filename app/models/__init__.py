"""SQLAlchemy 모델 re-export (지시서 §6).

Alembic autogenerate 및 애플리케이션 전역에서 `from app.models import *` /
`from app.models import Base, AuctionItem, ...` 형태로 사용할 수 있도록
모든 모델을 이 모듈에서 재노출한다.
"""

from app.models.auction_item import AuctionItem
from app.models.auction_result import AuctionResult
from app.models.base import Base
from app.models.collection_job import CollectionJob
from app.models.notification import Notification
from app.models.price_prediction import PricePrediction
from app.models.property_transaction import PropertyTransaction
from app.models.raw_source_record import RawSourceRecord
from app.models.real_estate_detail import RealEstateDetail
from app.models.risk_assessment import RiskAssessment
from app.models.saved_search import SavedSearch
from app.models.user import User
from app.models.user_watchlist import UserWatchlist
from app.models.vehicle_detail import VehicleDetail

__all__ = [
    "Base",
    "User",
    "AuctionItem",
    "RealEstateDetail",
    "VehicleDetail",
    "AuctionResult",
    "PricePrediction",
    "UserWatchlist",
    "SavedSearch",
    "RawSourceRecord",
    "PropertyTransaction",
    "RiskAssessment",
    "CollectionJob",
    "Notification",
]
