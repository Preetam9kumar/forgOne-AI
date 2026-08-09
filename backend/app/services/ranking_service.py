"""Adapts eligible suppliers' quotation + fact data into ranking engine input."""
from __future__ import annotations

from sqlalchemy.orm import Session

from app.models import Quotation, SupplierFact
from app.ranking.engine import rank_suppliers, sensitivity_analysis, DEFAULT_SENSITIVITY_SCENARIOS
from app.services.eligibility_service import screen_all


def _quality_score(db: Session, supplier_id: str) -> float | None:
    fact = (
        db.query(SupplierFact)
        .filter_by(supplier_id=supplier_id, field="sustainability_score")
        .first()
    )
    # Placeholder proxy until a dedicated quality_score field exists in the pack;
    # kept as its own function so swapping the source is a one-line change.
    return float(fact.value) if fact else None


def _eligible_supplier_rows(db: Session, product_id: str = "prod-001") -> tuple[list[dict], list[dict]]:
    """Returns (rows_for_ranking, screen_results) — screen_results included so
    callers can show *why* ineligible suppliers were excluded, not just drop them."""
    screen_results = screen_all(db, product_id)
    rows = []
    for result in screen_results:
        if not result["eligible"]:
            continue
        sid = result["supplier_id"]
        q = db.query(Quotation).filter_by(supplier_id=sid).first()
        sustainability = (
            db.query(SupplierFact)
            .filter_by(supplier_id=sid, field="sustainability_score")
            .first()
        )
        if q is None:
            continue
        rows.append({
            "supplier_id": sid,
            "price": q.unit_price,
            "lead_time_days": q.lead_time_days,
            "quality_score": float(sustainability.value) if sustainability else 3.0,
            "sustainability_score": float(sustainability.value) if sustainability else 3.0,
        })
    return rows, screen_results


def rank(db: Session, weights: dict | None = None, product_id: str = "prod-001") -> dict:
    rows, screen_results = _eligible_supplier_rows(db, product_id)
    ranked_df = rank_suppliers(rows, weights)
    excluded = [r for r in screen_results if not r["eligible"]]
    return {
        "ranked": ranked_df.reset_index().to_dict(orient="records"),
        "excluded": [
            {"supplier_id": r["supplier_id"], "supplier_name": r["supplier_name"],
             "reasons": [c["reason"] for c in r["checks"] if c["status"] != "pass"]}
            for r in excluded
        ],
    }


def sensitivity(db: Session, product_id: str = "prod-001") -> dict:
    rows, _ = _eligible_supplier_rows(db, product_id)
    df = sensitivity_analysis(rows, DEFAULT_SENSITIVITY_SCENARIOS)
    return {"scenarios": list(DEFAULT_SENSITIVITY_SCENARIOS.keys()), "ranks": df.reset_index().to_dict(orient="records")}


def baseline(db: Session, product_id: str = "prod-001") -> dict:
    """Simplest possible baseline: rank eligible suppliers by price alone.
    Required by the brief as the comparison point for the copilot's ranking."""
    rows, _ = _eligible_supplier_rows(db, product_id)
    ranked_df = rank_suppliers(rows, weights={"price": 1.0})
    return {"method": "price_only_baseline", "ranked": ranked_df.reset_index().to_dict(orient="records")}
