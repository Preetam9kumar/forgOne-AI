"""Weighted supplier ranking + sensitivity analysis — pure computation, no LLM.

Criteria are normalized to a common 0-1 scale (min-max, direction-aware) before
weighting, since raw price and raw lead-time live on incomparable scales.
Only ELIGIBLE suppliers (post-eligibility-screen) should ever be passed in here.
"""
from __future__ import annotations

import pandas as pd

DEFAULT_WEIGHTS: dict[str, float] = {
    "price": 0.35,
    "lead_time_days": 0.25,
    "quality_score": 0.25,
    "sustainability_score": 0.15,
}

# Criteria where a LOWER raw value is better (price, lead time).
# Everything else not listed here is treated as higher-is-better.
LOWER_IS_BETTER = {"price", "lead_time_days"}


def _normalize(series: pd.Series, lower_is_better: bool) -> pd.Series:
    lo, hi = series.min(), series.max()
    if pd.isna(lo) or pd.isna(hi) or hi == lo:
        # No spread (or all-NaN) across eligible suppliers on this criterion —
        # it can't discriminate, so treat everyone as tied on it.
        return pd.Series([1.0] * len(series), index=series.index)
    norm = (series - lo) / (hi - lo)
    return 1 - norm if lower_is_better else norm


def rank_suppliers(
    supplier_rows: list[dict],
    weights: dict[str, float] | None = None,
) -> pd.DataFrame:
    """supplier_rows: [{"supplier_id": ..., "price": ..., "lead_time_days": ...,
    "quality_score": ..., "sustainability_score": ...}, ...] — eligible suppliers only.

    Returns a DataFrame indexed by supplier_id with per-criterion normalized
    scores, a weighted total `score`, and an integer `rank` (1 = best).
    """
    weights = weights or DEFAULT_WEIGHTS
    if not supplier_rows:
        return pd.DataFrame(columns=["score", "rank"])

    df = pd.DataFrame(supplier_rows).set_index("supplier_id")

    total_weight = sum(w for c, w in weights.items() if c in df.columns) or 1.0
    score = pd.Series(0.0, index=df.index)
    for criterion, weight in weights.items():
        if criterion not in df.columns:
            continue
        norm = _normalize(df[criterion], lower_is_better=criterion in LOWER_IS_BETTER)
        df[f"{criterion}_norm"] = norm
        score += norm * (weight / total_weight)  # re-normalize so weights need not sum to 1

    df["score"] = score.round(4)
    df["rank"] = df["score"].rank(ascending=False, method="min").astype(int)
    return df.sort_values("rank")


def sensitivity_analysis(
    supplier_rows: list[dict],
    weight_scenarios: dict[str, dict[str, float]],
) -> pd.DataFrame:
    """Re-rank under each named weight scenario; return a DataFrame of
    supplier_id x scenario -> rank, so the UI can show rank movement."""
    ranks = {}
    for scenario_name, weights in weight_scenarios.items():
        ranked = rank_suppliers(supplier_rows, weights)
        ranks[scenario_name] = ranked["rank"]
    return pd.DataFrame(ranks)


DEFAULT_SENSITIVITY_SCENARIOS: dict[str, dict[str, float]] = {
    "balanced": DEFAULT_WEIGHTS,
    "cost_priority": {"price": 0.6, "lead_time_days": 0.15, "quality_score": 0.15, "sustainability_score": 0.10},
    "speed_priority": {"price": 0.15, "lead_time_days": 0.6, "quality_score": 0.15, "sustainability_score": 0.10},
    "sustainability_priority": {"price": 0.15, "lead_time_days": 0.15, "quality_score": 0.2, "sustainability_score": 0.5},
}
