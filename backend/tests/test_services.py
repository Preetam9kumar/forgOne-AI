from app.services import eligibility_service, ranking_service, explain_service


# ---- eligibility_service ----

def test_screen_aster_is_fully_eligible(seeded_db):
    result = eligibility_service.screen(seeded_db, "aster")
    assert result["eligible"] is True
    assert all(c["status"] == "pass" for c in result["checks"])


def test_screen_borealis_is_ineligible_due_to_missing_lead_time(seeded_db):
    result = eligibility_service.screen(seeded_db, "borealis")
    assert result["eligible"] is False
    lead_time_check = next(c for c in result["checks"] if c["field"] == "lead_time_days")
    assert lead_time_check["status"] == "insufficient_data"


def test_screen_crestpoint_is_ineligible_due_to_conflicting_capacity(seeded_db):
    result = eligibility_service.screen(seeded_db, "crestpoint")
    assert result["eligible"] is False
    capacity_check = next(c for c in result["checks"] if c["field"] == "capacity_units_per_month")
    assert capacity_check["status"] == "conflicting_data"


def test_screen_deltaforge_fails_certification_requirement(seeded_db):
    result = eligibility_service.screen(seeded_db, "deltaforge")
    assert result["eligible"] is False
    cert_check = next(c for c in result["checks"] if c["field"] == "certification")
    assert cert_check["status"] == "fail"


def test_screen_unknown_supplier_returns_none(seeded_db):
    assert eligibility_service.screen(seeded_db, "does-not-exist") is None


def test_screen_all_covers_every_supplier(seeded_db):
    results = eligibility_service.screen_all(seeded_db)
    assert {r["supplier_id"] for r in results} == {"aster", "borealis", "crestpoint", "deltaforge", "eastwind"}


# ---- ranking_service ----

def test_rank_only_includes_eligible_suppliers(seeded_db):
    result = ranking_service.rank(seeded_db)
    ranked_ids = {row["supplier_id"] for row in result["ranked"]}
    # only aster and eastwind pass every mandatory constraint in the sample pack
    assert ranked_ids == {"aster", "eastwind"}


def test_rank_reports_exclusion_reasons_for_ineligible_suppliers(seeded_db):
    result = ranking_service.rank(seeded_db)
    excluded_ids = {row["supplier_id"] for row in result["excluded"]}
    assert excluded_ids == {"borealis", "crestpoint", "deltaforge"}
    for row in result["excluded"]:
        assert len(row["reasons"]) >= 1


def test_baseline_ranks_by_price_only(seeded_db):
    result = ranking_service.baseline(seeded_db)
    ranked = result["ranked"]
    # aster ($12.50) should outrank eastwind ($16.20) on a price-only baseline
    aster_rank = next(r["rank"] for r in ranked if r["supplier_id"] == "aster")
    eastwind_rank = next(r["rank"] for r in ranked if r["supplier_id"] == "eastwind")
    assert aster_rank < eastwind_rank


def test_sensitivity_returns_all_default_scenarios(seeded_db):
    result = ranking_service.sensitivity(seeded_db)
    assert set(result["scenarios"]) == {"balanced", "cost_priority", "speed_priority", "sustainability_priority"}


# ---- explain_service ----

def test_explain_supplier_grounds_in_evidence_chunk(seeded_db):
    result = explain_service.explain_supplier(seeded_db, "aster", "certification")
    assert result["citations"], "expected at least one citation"
    assert result["citations"][0]["doc_id"] == "Aster_Supplier_Profile.pdf"


def test_explain_supplier_with_no_matching_evidence_returns_not_found(seeded_db):
    result = explain_service.explain_supplier(seeded_db, "borealis", "packaging_materials")
    assert result["explanation"] == "Not found in source."
