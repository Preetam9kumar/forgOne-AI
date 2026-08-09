import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from app.api.main import app
from app.db import get_db
from app.models import Base
from app.ingest.pipeline import ingest_pack


@pytest.fixture()
def client(sample_pack):
    # StaticPool is required here: FastAPI runs sync `def` endpoints in a
    # worker thread, and SQLite's default per-thread connection would hand
    # that thread a brand-new (tableless) in-memory database otherwise.
    engine = create_engine(
        "sqlite:///:memory:",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )
    Base.metadata.create_all(bind=engine)
    TestingSession = sessionmaker(bind=engine)
    session = TestingSession()
    ingest_pack(session, sample_pack)
    session.close()

    def override_get_db():
        db = TestingSession()
        try:
            yield db
        finally:
            db.close()

    app.dependency_overrides[get_db] = override_get_db
    with TestClient(app) as c:
        yield c
    app.dependency_overrides.clear()


def test_health(client):
    resp = client.get("/health")
    assert resp.status_code == 200
    assert resp.json() == {"status": "ok"}


def test_metrics_endpoint_exposes_runtime_stats(client):
    resp = client.get("/metrics")
    assert resp.status_code == 200
    body = resp.json()
    assert body["uptime_seconds"] >= 0.0
    assert body["request_count"] >= 1
    assert "average_response_time_ms" in body


def test_get_all_eligibility(client):
    resp = client.get("/eligibility")
    assert resp.status_code == 200
    body = resp.json()
    assert len(body) == 5
    eligible = {r["supplier_id"] for r in body if r["eligible"]}
    assert eligible == {"aster", "eastwind"}


def test_get_single_supplier_eligibility(client):
    resp = client.get("/suppliers/aster/eligibility")
    assert resp.status_code == 200
    assert resp.json()["eligible"] is True


def test_get_unknown_supplier_eligibility_returns_404(client):
    resp = client.get("/suppliers/nope/eligibility")
    assert resp.status_code == 404


def test_ingest_endpoint_accepts_raw_pack_payload(client, sample_pack):
    resp = client.post("/ingest", json=sample_pack)
    assert resp.status_code == 200
    body = resp.json()
    assert body["suppliers_loaded"] == 5
    assert body["facts_loaded"] > 0
    assert body["evidence_chunks_loaded"] > 0


def test_ingest_endpoint_rejects_malformed_payload(client):
    resp = client.post("/ingest", json={"invalid": "payload"})
    assert resp.status_code == 422


def test_get_rankings_only_eligible_suppliers(client):
    resp = client.get("/rankings")
    assert resp.status_code == 200
    body = resp.json()
    ranked_ids = {row["supplier_id"] for row in body["ranked"]}
    assert ranked_ids == {"aster", "eastwind"}
    assert len(body["excluded"]) == 3


def test_get_rankings_with_custom_weights(client):
    resp = client.get("/rankings", params={"w_price": 1.0, "w_lead_time": 0, "w_quality": 0, "w_sustainability": 0})
    assert resp.status_code == 200
    ranked = resp.json()["ranked"]
    # cheapest of the two eligible suppliers (aster $12.50 vs eastwind $16.20) should be rank 1
    top = next(r for r in ranked if r["rank"] == 1)
    assert top["supplier_id"] == "aster"


def test_get_sensitivity(client):
    resp = client.get("/rankings/sensitivity")
    assert resp.status_code == 200
    assert "cost_priority" in resp.json()["scenarios"]


def test_get_baseline(client):
    resp = client.get("/rankings/baseline")
    assert resp.status_code == 200
    assert resp.json()["method"] == "price_only_baseline"


def test_explain_endpoint_requires_criterion_param(client):
    resp = client.get("/suppliers/aster/explain")
    assert resp.status_code == 422  # missing required query param


def test_explain_endpoint_returns_grounded_explanation(client):
    resp = client.get("/suppliers/aster/explain", params={"criterion": "certification"})
    assert resp.status_code == 200
    body = resp.json()
    assert body["citations"]
    assert body["explanation"] != "Not found in source."


def test_no_endpoint_exists_for_supplier_approval_or_contact(client):
    # Structural enforcement of the brief's human-approval boundary: assert
    # the route table contains no write path other than /ingest.
    routes = {getattr(route, "path", "") for route in client.app.routes}
    forbidden_terms = ["approve", "contact", "order", "purchase", "rfq"]
    assert not any(term in route.lower() for route in routes for term in forbidden_terms)
