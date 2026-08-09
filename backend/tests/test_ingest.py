from app.models import Product, Supplier, SupplierFact, Quotation, EvidenceChunk
from app.ingest.pipeline import ingest_pack


def test_ingest_pack_loads_expected_counts(db_session, sample_pack):
    summary = ingest_pack(db_session, sample_pack)
    assert summary["suppliers_loaded"] == 5
    assert summary["product_id"] == "prod-001"
    assert summary["facts_loaded"] > 0
    assert summary["evidence_chunks_loaded"] > 0


def test_ingest_pack_persists_product_and_requirements(seeded_db):
    product = seeded_db.get(Product, "prod-001")
    assert product is not None
    assert product.name == "Precision Enclosure Assembly"
    assert len(product.requirements) == 4


def test_ingest_pack_persists_suppliers(seeded_db):
    suppliers = seeded_db.query(Supplier).all()
    ids = {s.id for s in suppliers}
    assert ids == {"aster", "borealis", "crestpoint", "deltaforge", "eastwind"}


def test_ingest_pack_preserves_conflicting_facts_as_separate_rows(seeded_db):
    facts = (
        seeded_db.query(SupplierFact)
        .filter_by(supplier_id="crestpoint", field="capacity_units_per_month")
        .all()
    )
    # Both conflicting values must survive ingestion — nothing gets silently deduped.
    assert len(facts) == 2
    values = {f.value for f in facts}
    assert values == {4000, 6500}


def test_ingest_pack_leaves_missing_fact_absent_not_defaulted(seeded_db):
    facts = (
        seeded_db.query(SupplierFact)
        .filter_by(supplier_id="borealis", field="lead_time_days")
        .all()
    )
    assert facts == []  # no row at all, not a null/zero placeholder


def test_ingest_pack_loads_quotations(seeded_db):
    q = seeded_db.query(Quotation).filter_by(supplier_id="aster").first()
    assert q.unit_price == 12.50
    assert q.incoterm == "FOB"


def test_ingest_pack_loads_evidence_chunks_with_citation_metadata(seeded_db):
    chunks = seeded_db.query(EvidenceChunk).filter_by(supplier_id="aster").all()
    assert len(chunks) >= 1
    assert all(c.doc_id and c.source_field for c in chunks)
