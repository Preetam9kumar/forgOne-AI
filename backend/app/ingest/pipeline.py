"""Ingests a challenge-pack-shaped JSON file into the database.

In production this is where you'd also: copy raw source files to Blob
Storage, compute SHA-256 checksums into a source_manifest.json, chunk +
embed free-text evidence, and upsert into Azure AI Search. Those steps are
infra-dependent (need live Azure); they're isolated in ingest/azure_sync.py
so this module stays testable with zero external dependencies.
"""
from __future__ import annotations

import hashlib
import json
from pathlib import Path

from sqlalchemy.orm import Session

from app.config import settings
from app.ingest.azure_sync import sync_evidence_chunks
from app.ingest.schemas import ChallengePackSchema
from app.models import (
    Product,
    Requirement,
    Supplier,
    SupplierFact,
    Quotation,
    EvidenceChunk,
)


def compute_checksum(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def load_pack(path: str | Path) -> dict:
    path = Path(path)
    with open(path, "r") as f:
        return json.load(f)


def ingest_pack(db: Session, pack: dict | ChallengePackSchema) -> dict:
    """Idempotent-ish load: clears existing rows for the product/suppliers in
    this pack, then inserts fresh. Returns a small summary dict."""
    if not isinstance(pack, ChallengePackSchema):
        pack = ChallengePackSchema.model_validate(pack)

    product_data = pack.product

    inserted_chunks: list[EvidenceChunk] = []
    with db.begin():
        db.query(Requirement).filter_by(product_id=product_data.id).delete()
        db.query(Product).filter_by(id=product_data.id).delete()

        product = Product(id=product_data.id, name=product_data.name)
        db.add(product)
        for r in product_data.requirements:
            db.add(Requirement(
                product_id=product.id,
                field=r.field,
                operator=r.operator,
                value=r.value,
                mandatory=r.mandatory,
            ))

        supplier_count, fact_count, chunk_count = 0, 0, 0
        for s in pack.suppliers:
            db.query(SupplierFact).filter_by(supplier_id=s.id).delete()
            db.query(Quotation).filter_by(supplier_id=s.id).delete()
            db.query(EvidenceChunk).filter_by(supplier_id=s.id).delete()
            db.query(Supplier).filter_by(id=s.id).delete()

            supplier = Supplier(id=s.id, name=s.name, location=s.location)
            db.add(supplier)
            supplier_count += 1

            for fact in s.facts:
                db.add(SupplierFact(
                    supplier_id=supplier.id,
                    field=fact.field,
                    value=fact.value,
                    source_doc=fact.source_doc,
                    source_field=fact.source_field,
                    confidence=fact.confidence,
                ))
                fact_count += 1

            q = s.quotation
            if q:
                db.add(Quotation(
                    supplier_id=supplier.id,
                    unit_price=q.unit_price,
                    currency=q.currency,
                    moq=q.moq,
                    lead_time_days=q.lead_time_days,
                    incoterm=q.incoterm,
                    valid_until=q.valid_until,
                ))

            for chunk in s.evidence_text:
                evidence_chunk = EvidenceChunk(
                    supplier_id=supplier.id,
                    doc_id=chunk.doc_id,
                    source_field=chunk.source_field,
                    content=chunk.content,
                )
                db.add(evidence_chunk)
                inserted_chunks.append(evidence_chunk)
                chunk_count += 1

    summary = {
        "product_id": product.id,
        "suppliers_loaded": supplier_count,
        "facts_loaded": fact_count,
        "evidence_chunks_loaded": chunk_count,
    }

    if settings.azure_rag_enabled and inserted_chunks:
        # Keep the DB insert path separate from the Azure Search sync path.
        sync_evidence_chunks(inserted_chunks)

    return summary


def ingest_from_file(db: Session, path: str | Path) -> dict:
    pack = load_pack(path)
    summary = ingest_pack(db, pack)
    summary["checksum_sha256"] = compute_checksum(Path(path))
    return summary
