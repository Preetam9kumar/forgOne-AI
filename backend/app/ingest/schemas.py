from __future__ import annotations

from typing import Any, Literal

from pydantic import BaseModel


class RequirementSchema(BaseModel):
    field: str
    operator: Literal[">=", "<=", "==", "in", "contains"]
    value: Any
    mandatory: bool = True


class SupplierFactSchema(BaseModel):
    field: str
    value: Any
    source_doc: str
    source_field: str
    confidence: float = 1.0


class QuotationSchema(BaseModel):
    unit_price: float | None = None
    currency: str = "USD"
    moq: int | None = None
    lead_time_days: int | None = None
    incoterm: str | None = None
    valid_until: str | None = None


class EvidenceChunkSchema(BaseModel):
    doc_id: str
    source_field: str
    content: str


class SupplierSchema(BaseModel):
    id: str
    name: str
    location: str | None = None
    facts: list[SupplierFactSchema] = []
    quotation: QuotationSchema | None = None
    evidence_text: list[EvidenceChunkSchema] = []


class ProductSchema(BaseModel):
    id: str
    name: str
    requirements: list[RequirementSchema]


class ChallengePackSchema(BaseModel):
    product: ProductSchema
    suppliers: list[SupplierSchema]
