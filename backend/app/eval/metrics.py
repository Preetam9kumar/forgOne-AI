"""Computes the metrics the challenge brief requires teams to report.
Pure functions over already-computed results -- no DB or LLM calls here,
so these are cheap to run repeatedly in CI against the golden/held-out set.
"""
from __future__ import annotations


def constraint_satisfaction_rate(screen_results: list[dict]) -> float:
    """Fraction of (supplier, requirement) checks that resolved to PASS or
    a definitive FAIL -- i.e. the fraction NOT stuck in insufficient/conflicting
    data. High values here mean the eligibility screen had enough source
    data to make a clean call most of the time."""
    total, resolved = 0, 0
    for r in screen_results:
        for c in r["checks"]:
            total += 1
            if c["status"] in ("pass", "fail"):
                resolved += 1
    return resolved / total if total else 0.0


def citation_coverage(explanations: list[dict]) -> float:
    """Fraction of explanation outputs that carry at least one citation.
    An explanation with zero citations is either an ungrounded claim or a
    correctly-declined 'Not found in source.' -- both count as *not covered*
    for this metric, since neither has verifiable source backing."""
    if not explanations:
        return 0.0
    with_citation = sum(1 for e in explanations if e.get("citations"))
    return with_citation / len(explanations)


def ranking_agreement(copilot_ranked_ids: list[str], reference_ranked_ids: list[str]) -> float:
    """Spearman-style agreement: fraction of pairwise orderings the two
    rankings agree on, restricted to suppliers present in both lists."""
    common = [s for s in copilot_ranked_ids if s in reference_ranked_ids]
    if len(common) < 2:
        return 1.0 if common == copilot_ranked_ids == reference_ranked_ids else 0.0

    copilot_pos = {s: i for i, s in enumerate(copilot_ranked_ids) if s in common}
    reference_pos = {s: i for i, s in enumerate(reference_ranked_ids) if s in common}

    agree, total_pairs = 0, 0
    for i in range(len(common)):
        for j in range(i + 1, len(common)):
            a, b = common[i], common[j]
            total_pairs += 1
            same_order_copilot = copilot_pos[a] < copilot_pos[b]
            same_order_reference = reference_pos[a] < reference_pos[b]
            if same_order_copilot == same_order_reference:
                agree += 1
    return agree / total_pairs if total_pairs else 1.0


def numeric_error(predicted: dict[str, float], reference: dict[str, float]) -> dict[str, float]:
    """Mean absolute error for numeric fields (cost, lead time) that have a
    known reference value, keyed by supplier_id."""
    errors = [abs(predicted[k] - reference[k]) for k in reference if k in predicted]
    return {
        "mean_absolute_error": sum(errors) / len(errors) if errors else 0.0,
        "n_compared": len(errors),
    }
