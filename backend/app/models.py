"""SQLAlchemy ORM models — the Postgres schema from the architecture doc,
runnable locally against SQLite (see app/db.py)."""
from __future__ import annotations

from sqlalchemy import (
    Column, String, Float, Integer, Boolean, ForeignKey, JSON, DateTime
)
from sqlalchemy.orm import declarative_base, relationship
from datetime import datetime, timezone

Base = declarative_base()


def utcnow():
    return datetime.now(timezone.utc)


class Product(Base):
    __tablename__ = "products"
    id = Column(String, primary_key=True)
    name = Column(String, nullable=False)
    requirements = relationship("Requirement", back_populates="product")


class Requirement(Base):
    __tablename__ = "requirements"
    id = Column(Integer, primary_key=True, autoincrement=True)
    product_id = Column(String, ForeignKey("products.id"), nullable=False)
    field = Column(String, nullable=False)
    operator = Column(String, nullable=False)  # one of >=, <=, ==, in, contains
    value = Column(JSON, nullable=False)
    mandatory = Column(Boolean, default=True)
    product = relationship("Product", back_populates="requirements")


class Supplier(Base):
    __tablename__ = "suppliers"
    id = Column(String, primary_key=True)
    name = Column(String, nullable=False)
    location = Column(String)
    facts = relationship("SupplierFact", back_populates="supplier")
    quotation = relationship("Quotation", back_populates="supplier", uselist=False)


class SupplierFact(Base):
    """Structured, computable form of a fact. One (field, source_doc) pair per row —
    multiple rows for the same field with different source_doc/value means conflicting
    source data, which the eligibility engine must surface rather than silently resolve."""
    __tablename__ = "supplier_facts"
    id = Column(Integer, primary_key=True, autoincrement=True)
    supplier_id = Column(String, ForeignKey("suppliers.id"), nullable=False)
    field = Column(String, nullable=False)
    value = Column(JSON, nullable=False)
    source_doc = Column(String, nullable=False)
    source_field = Column(String, nullable=False)
    confidence = Column(Float, default=1.0)
    retrieved_at = Column(DateTime, default=utcnow)
    supplier = relationship("Supplier", back_populates="facts")


class Quotation(Base):
    __tablename__ = "quotations"
    id = Column(Integer, primary_key=True, autoincrement=True)
    supplier_id = Column(String, ForeignKey("suppliers.id"), nullable=False)
    unit_price = Column(Float)
    currency = Column(String, default="USD")
    moq = Column(Integer)
    lead_time_days = Column(Integer, nullable=True)
    incoterm = Column(String)
    valid_until = Column(String)
    supplier = relationship("Supplier", back_populates="quotation")


class EvidenceChunk(Base):
    """Unstructured/free-text form of evidence, for the RAG explanation layer.
    Mirrors what would be embedded and pushed to Azure AI Search."""
    __tablename__ = "evidence_chunks"
    id = Column(Integer, primary_key=True, autoincrement=True)
    supplier_id = Column(String, ForeignKey("suppliers.id"), nullable=False)
    doc_id = Column(String, nullable=False)
    source_field = Column(String, nullable=False)
    content = Column(String, nullable=False)


class EvaluationRun(Base):
    __tablename__ = "evaluation_runs"
    id = Column(Integer, primary_key=True, autoincrement=True)
    metric = Column(String, nullable=False)
    value = Column(Float, nullable=False)
    notes = Column(String)
    created_at = Column(DateTime, default=utcnow)
