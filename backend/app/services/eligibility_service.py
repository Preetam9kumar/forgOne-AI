"""Adapts DB rows into the eligibility engine's plain data types, and back
into JSON-friendly dicts for the API layer."""
from __future__ import annotations

from sqlalchemy.orm import Session

from app.models import Product, Supplier, SupplierFact
from app.eligibility.engine import (
    FactValue,
    Requirement,
    screen_supplier,
    is_eligible,
)


def _facts_by_field(db: Session, supplier_id: str) -> dict[str, list[FactValue]]:
    rows = db.query(SupplierFact).filter_by(supplier_id=supplier_id).all()
    out: dict[str, list[FactValue]] = {}
    for r in rows:
        out.setdefault(r.field, []).append(
            FactValue(value=r.value, source_doc=r.source_doc, source_field=r.source_field, confidence=r.confidence)
        )
    return out


def _requirements(db: Session, product_id: str) -> list[Requirement]:
    product = db.get(Product, product_id)
    if product is None:
        return []
    return [
        Requirement(field=r.field, operator=r.operator, value=r.value, mandatory=r.mandatory)
        for r in product.requirements
    ]


def screen(db: Session, supplier_id: str, product_id: str = "prod-001") -> dict | None:
    supplier = db.get(Supplier, supplier_id)
    if supplier is None:
        return None
    requirements = _requirements(db, product_id)
    facts = _facts_by_field(db, supplier_id)
    results = screen_supplier(supplier_id, requirements, facts)
    return {
        "supplier_id": supplier_id,
        "supplier_name": supplier.name,
        "eligible": is_eligible(results),
        "checks": [
            {
                "field": r.requirement_field,
                "operator": r.operator,
                "required_value": r.required_value,
                "status": r.status.value,
                "reason": r.reason,
            }
            for r in results
        ],
    }


def screen_all(db: Session, product_id: str = "prod-001") -> list[dict]:
    supplier_ids = [s.id for s in db.query(Supplier).all()]
    return [screen(db, sid, product_id) for sid in supplier_ids]
