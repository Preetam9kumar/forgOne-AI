from app.eval.metrics import (
    constraint_satisfaction_rate,
    citation_coverage,
    ranking_agreement,
    numeric_error,
)


def test_constraint_satisfaction_rate_counts_pass_and_fail_as_resolved():
    screen_results = [
        {"checks": [{"status": "pass"}, {"status": "fail"}]},
        {"checks": [{"status": "insufficient_data"}]},
    ]
    # 2 resolved (pass, fail) out of 3 total checks
    assert constraint_satisfaction_rate(screen_results) == 2 / 3


def test_constraint_satisfaction_rate_handles_empty_input():
    assert constraint_satisfaction_rate([]) == 0.0


def test_citation_coverage_counts_only_explanations_with_citations():
    explanations = [
        {"explanation": "x", "citations": [{"doc_id": "a.pdf", "source_field": "f"}]},
        {"explanation": "Not found in source.", "citations": []},
    ]
    assert citation_coverage(explanations) == 0.5


def test_ranking_agreement_is_1_for_identical_order():
    assert ranking_agreement(["a", "b", "c"], ["a", "b", "c"]) == 1.0


def test_ranking_agreement_is_0_for_fully_reversed_order():
    assert ranking_agreement(["a", "b", "c"], ["c", "b", "a"]) == 0.0


def test_ranking_agreement_partial_disagreement():
    # one adjacent swap out of 3 pairs disagrees
    result = ranking_agreement(["a", "b", "c"], ["b", "a", "c"])
    assert 0.0 < result < 1.0


def test_numeric_error_computes_mean_absolute_error():
    predicted = {"aster": 12.50, "eastwind": 16.00}
    reference = {"aster": 12.50, "eastwind": 16.20}
    result = numeric_error(predicted, reference)
    assert round(result["mean_absolute_error"], 4) == 0.1
    assert result["n_compared"] == 2
