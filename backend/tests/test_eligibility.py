from app.eligibility.engine import (
    FactValue,
    Requirement,
    EligibilityStatus,
    evaluate_requirement,
    screen_supplier,
    is_eligible,
)


def test_pass_when_fact_satisfies_operator():
    req = Requirement(field="capacity_units_per_month", operator=">=", value=5000)
    facts = [FactValue(8000, "profile.pdf", "monthly_capacity")]
    result = evaluate_requirement("aster", req, facts)
    assert result.status == EligibilityStatus.PASS
    assert "profile.pdf" in result.reason


def test_fail_when_fact_does_not_satisfy_operator():
    req = Requirement(field="lead_time_days", operator="<=", value=45)
    facts = [FactValue(60, "quote.pdf", "lead_time")]
    result = evaluate_requirement("x", req, facts)
    assert result.status == EligibilityStatus.FAIL


def test_insufficient_data_when_no_facts():
    req = Requirement(field="lead_time_days", operator="<=", value=45)
    result = evaluate_requirement("borealis", req, [])
    assert result.status == EligibilityStatus.INSUFFICIENT_DATA
    assert result.evidence == []


def test_conflicting_data_when_sources_disagree():
    req = Requirement(field="capacity_units_per_month", operator=">=", value=5000)
    facts = [
        FactValue(4000, "profile.pdf", "monthly_capacity"),
        FactValue(6500, "rfq_response.pdf", "stated_capacity"),
    ]
    result = evaluate_requirement("crestpoint", req, facts)
    assert result.status == EligibilityStatus.CONFLICTING_DATA
    assert len(result.evidence) == 2
    assert "profile.pdf" in result.reason and "rfq_response.pdf" in result.reason


def test_contains_operator_checks_membership_in_list():
    req = Requirement(field="certification", operator="contains", value="ISO9001")
    facts = [FactValue(["ISO9001", "ISO14001"], "profile.pdf", "certifications")]
    result = evaluate_requirement("aster", req, facts)
    assert result.status == EligibilityStatus.PASS


def test_contains_operator_fails_when_missing_from_list():
    req = Requirement(field="certification", operator="contains", value="ISO9001")
    facts = [FactValue(["ISO14001"], "profile.pdf", "certifications")]
    result = evaluate_requirement("deltaforge", req, facts)
    assert result.status == EligibilityStatus.FAIL


def test_screen_supplier_only_evaluates_mandatory_requirements():
    reqs = [
        Requirement(field="capacity_units_per_month", operator=">=", value=5000, mandatory=True),
        Requirement(field="nice_to_have", operator=">=", value=1, mandatory=False),
    ]
    facts_by_field = {"capacity_units_per_month": [FactValue(8000, "p.pdf", "cap")]}
    results = screen_supplier("aster", reqs, facts_by_field)
    assert len(results) == 1
    assert results[0].requirement_field == "capacity_units_per_month"


def test_is_eligible_true_only_when_all_pass():
    all_pass = [
        evaluate_requirement("s", Requirement("a", ">=", 1), [FactValue(2, "d", "f")]),
        evaluate_requirement("s", Requirement("b", ">=", 1), [FactValue(2, "d", "f")]),
    ]
    assert is_eligible(all_pass) is True


def test_is_eligible_false_if_any_fail_or_insufficient_or_conflicting():
    one_missing = [
        evaluate_requirement("s", Requirement("a", ">=", 1), [FactValue(2, "d", "f")]),
        evaluate_requirement("s", Requirement("b", ">=", 1), []),  # insufficient data
    ]
    assert is_eligible(one_missing) is False


def test_boundary_value_is_inclusive():
    req = Requirement(field="lead_time_days", operator="<=", value=45)
    facts = [FactValue(45, "quote.pdf", "lead_time")]
    result = evaluate_requirement("x", req, facts)
    assert result.status == EligibilityStatus.PASS
