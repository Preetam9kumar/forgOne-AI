from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.db import get_db
from app.config import settings
from app.services import ranking_service

router = APIRouter(tags=["rankings"])


@router.get("/rankings")
def get_rankings(
    w_price: float = settings.default_price_weight,
    w_lead_time: float = settings.default_lead_time_weight,
    w_quality: float = settings.default_quality_weight,
    w_sustainability: float = settings.default_sustainability_weight,
    db: Session = Depends(get_db),
):
    weights = {
        "price": w_price,
        "lead_time_days": w_lead_time,
        "quality_score": w_quality,
        "sustainability_score": w_sustainability,
    }
    return ranking_service.rank(db, weights)


@router.get("/rankings/sensitivity")
def get_sensitivity(db: Session = Depends(get_db)):
    return ranking_service.sensitivity(db)


@router.get("/rankings/baseline")
def get_baseline(db: Session = Depends(get_db)):
    return ranking_service.baseline(db)
