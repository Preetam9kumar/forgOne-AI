import pandas as pd
from app.ranking.engine import (
    rank_suppliers,
    sensitivity_analysis,
    DEFAULT_WEIGHTS,
)

SAMPLE_ROWS = [
    {"supplier_id": "aster", "price": 12.50, "lead_time_days": 30, "quality_score": 4, "sustainability_score": 4},
    {"supplier_id": "crestpoint", "price": 9.80, "lead_time_days": 40, "quality_score": 3, "sustainability_score": 3},
    {"supplier_id": "deltaforge", "price": 8.90, "lead_time_days": 25, "quality_score": 3.5, "sustainability_score": 4},
    {"supplier_id": "eastwind", "price": 16.20, "lead_time_days": 22, "quality_score": 4.5, "sustainability_score": 5},
]


def test_rank_suppliers_returns_one_row_per_supplier():
    ranked = rank_suppliers(SAMPLE_ROWS)
    assert len(ranked) == 4
    assert set(ranked.index) == {"aster", "crestpoint", "deltaforge", "eastwind"}


def test_lower_price_scores_better_all_else_equal():
    rows = [
        {"supplier_id": "cheap", "price": 5.0, "lead_time_days": 30, "quality_score": 3, "sustainability_score": 3},
        {"supplier_id": "expensive", "price": 20.0, "lead_time_days": 30, "quality_score": 3, "sustainability_score": 3},
    ]
    ranked = rank_suppliers(rows, weights={"price": 1.0})
    assert ranked.loc["cheap", "rank"] == 1
    assert ranked.loc["expensive", "rank"] == 2


def test_rank_1_is_best_score():
    ranked = rank_suppliers(SAMPLE_ROWS)
    best = ranked.sort_values("score", ascending=False).index[0]
    assert ranked.loc[best, "rank"] == 1


def test_empty_input_returns_empty_frame():
    ranked = rank_suppliers([])
    assert ranked.empty


def test_no_spread_criterion_does_not_crash_and_ties_everyone():
    rows = [
        {"supplier_id": "a", "price": 10, "lead_time_days": 30, "quality_score": 3, "sustainability_score": 3},
        {"supplier_id": "b", "price": 10, "lead_time_days": 30, "quality_score": 3, "sustainability_score": 3},
    ]
    ranked = rank_suppliers(rows)
    assert ranked.loc["a", "score"] == ranked.loc["b", "score"]


def test_sensitivity_analysis_changes_rank_order_across_scenarios():
    scenarios = {
        "cost_priority": {"price": 1.0},
        "speed_priority": {"lead_time_days": 1.0},
    }
    result = sensitivity_analysis(SAMPLE_ROWS, scenarios)
    # cheapest supplier should rank #1 under cost priority
    assert result.loc["deltaforge", "cost_priority"] == 1
    # fastest lead time (lowest days) should rank #1 under speed priority
    assert result.loc["eastwind", "speed_priority"] == 1
    # the two scenarios should NOT produce identical orderings here
    assert not result["cost_priority"].equals(result["speed_priority"])


def test_weights_need_not_sum_to_one():
    # weights of {"price": 3.5} vs {"price": 0.35} should rank identically
    # since scoring re-normalizes by total active weight.
    r1 = rank_suppliers(SAMPLE_ROWS, weights={"price": 0.35})
    r2 = rank_suppliers(SAMPLE_ROWS, weights={"price": 3.5})
    assert r1["rank"].equals(r2["rank"])
