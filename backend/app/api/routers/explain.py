from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session

from app.db import get_db
from app.services import explain_service

router = APIRouter(tags=["explain"])


@router.get("/suppliers/{supplier_id}/explain")
def explain_supplier(
    supplier_id: str,
    criterion: str = Query(..., description="e.g. certification, lead_time_days, sustainability_score"),
    db: Session = Depends(get_db),
):
    return explain_service.explain_supplier(db, supplier_id, criterion)
