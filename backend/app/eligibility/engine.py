"""Deterministic eligibility screening — no LLM involved.

This is intentionally boring: every decision here must be exact, reproducible,
and traceable to a source fact, since it gates which suppliers ever reach the
ranking stage. Missing or conflicting source data is surfaced explicitly
rather than silently resolved (per the challenge brief's requirement).
"""
from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum
from typing import Any


class EligibilityStatus(str, Enum):
    PASS = "pass"
    FAIL = "fail"
    INSUFFICIENT_DATA = "insufficient_data"
    CONFLICTING_DATA = "conflicting_data"


@dataclass(frozen=True)
class FactValue:
    value: Any
    source_doc: str
    source_field: str
    confidence: float = 1.0


@dataclass(frozen=True)
class Requirement:
    field: str
    operator: str  # one of: >=, <=, ==, in, contains
    value: Any
    mandatory: bool = True


@dataclass
class EligibilityCheckResult:
    supplier_id: str
    requirement_field: str
    operator: str
    required_value: Any
    status: EligibilityStatus
    evidence: list[FactValue] = field(default_factory=list)
    reason: str = ""


def _op_contains(fact_value, required_value) -> bool:
    # fact_value is expected to be a list (e.g. certifications); required_value a single item.
    if isinstance(fact_value, (list, tuple, set)):
        return required_value in fact_value
    return required_value in str(fact_value)


OPERATORS = {
    ">=": lambda a, b: a is not None and a >= b,
    "<=": lambda a, b: a is not None and a <= b,
    "==": lambda a, b: a == b,
    "in": lambda a, b: a in b,
    "contains": _op_contains,
}


def evaluate_requirement(
    supplier_id: str,
    requirement: Requirement,
    facts_for_field: list[FactValue],
) -> EligibilityCheckResult:
    """Evaluate a single mandatory requirement for a single supplier.

    Precedence: no data -> INSUFFICIENT_DATA; conflicting values across
    sources -> CONFLICTING_DATA; otherwise PASS/FAIL from the operator.
    Both non-PASS-non-FAIL states exclude the supplier from ranking but are
    reported with distinct, actionable reasons rather than collapsed into
    a generic failure.
    """
    if not facts_for_field:
        return EligibilityCheckResult(
            supplier_id=supplier_id,
            requirement_field=requirement.field,
            operator=requirement.operator,
            required_value=requirement.value,
            status=EligibilityStatus.INSUFFICIENT_DATA,
            evidence=[],
            reason=f"No source data found for '{requirement.field}'.",
        )

    # Detect conflicting values across sources (compare via repr for list/dict safety).
    distinct = {repr(f.value) for f in facts_for_field}
    if len(distinct) > 1:
        detail = ", ".join(f"{f.value!r} ({f.source_doc})" for f in facts_for_field)
        return EligibilityCheckResult(
            supplier_id=supplier_id,
            requirement_field=requirement.field,
            operator=requirement.operator,
            required_value=requirement.value,
            status=EligibilityStatus.CONFLICTING_DATA,
            evidence=list(facts_for_field),
            reason=f"Conflicting values for '{requirement.field}': {detail}",
        )

    fact = facts_for_field[0]
    op_fn = OPERATORS[requirement.operator]
    try:
        passed = bool(op_fn(fact.value, requirement.value))
    except TypeError:
        passed = False

    status = EligibilityStatus.PASS if passed else EligibilityStatus.FAIL
    verb = "satisfies" if passed else "fails"
    reason = (
        f"{requirement.field}={fact.value!r} {verb} {requirement.operator} "
        f"{requirement.value!r} [source: {fact.source_doc} / {fact.source_field}]"
    )
    return EligibilityCheckResult(
        supplier_id=supplier_id,
        requirement_field=requirement.field,
        operator=requirement.operator,
        required_value=requirement.value,
        status=status,
        evidence=[fact],
        reason=reason,
    )


def screen_supplier(
    supplier_id: str,
    requirements: list[Requirement],
    facts_by_field: dict[str, list[FactValue]],
) -> list[EligibilityCheckResult]:
    """Run every mandatory requirement against one supplier's facts."""
    return [
        evaluate_requirement(supplier_id, req, facts_by_field.get(req.field, []))
        for req in requirements
        if req.mandatory
    ]


def is_eligible(results: list[EligibilityCheckResult]) -> bool:
    """A supplier is eligible only if every mandatory check PASSed.
    FAIL, INSUFFICIENT_DATA, and CONFLICTING_DATA all exclude it from ranking —
    they are different reasons, not different outcomes."""
    return all(r.status == EligibilityStatus.PASS for r in results)
