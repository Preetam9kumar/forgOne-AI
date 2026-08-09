from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.db import get_db
from app.services import eligibility_service

router = APIRouter(tags=["eligibility"])


@router.get("/eligibility")
def get_all_eligibility(db: Session = Depends(get_db)):
    return eligibility_service.screen_all(db)


@router.get("/suppliers/{supplier_id}/eligibility")
def get_supplier_eligibility(supplier_id: str, db: Session = Depends(get_db)):
    result = eligibility_service.screen(db, supplier_id)
    if result is None:
        raise HTTPException(status_code=404, detail=f"Supplier '{supplier_id}' not found")
    return result
