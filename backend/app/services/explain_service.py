"""Wires the RAG explanation chain to the DB-backed evidence chunks.
Uses the real Azure hybrid retrieval chain when Azure endpoints are configured.
Otherwise it falls back to an in-DB keyword retriever + deterministic echo
LLM so /explain works without any cloud setup."""
from __future__ import annotations

import logging

from sqlalchemy.orm import Session

from app.config import settings
from app.models import EvidenceChunk
from app.rag.chain import RetrievedChunk, explain, build_azure_chain

logger = logging.getLogger(__name__)


class _DbKeywordRetriever:
    """Minimal fallback retriever: keyword-matches evidence_chunks in the DB.
    This is intentionally simple -- it exists so /explain works without any
    Azure AI Search deployment. Swap for the real hybrid retriever in prod."""

    def __init__(self, db: Session):
        self.db = db

    def retrieve(self, query: str, supplier_id: str, k: int = 5) -> list[RetrievedChunk]:
        rows = self.db.query(EvidenceChunk).filter_by(supplier_id=supplier_id).all()
        terms = [t.lower() for t in query.split() if len(t) > 3]
        scored = []
        for r in rows:
            content_lower = r.content.lower()
            score = sum(1 for t in terms if t in content_lower)
            if score > 0:
                scored.append((score, r))
        scored.sort(key=lambda pair: pair[0], reverse=True)
        return [
            RetrievedChunk(content=r.content, doc_id=r.doc_id, source_field=r.source_field, supplier_id=supplier_id)
            for _, r in scored[:k]
        ]


class _EchoLLM:
    """Deterministic stand-in LLM for offline/demo use: states the retrieved
    facts plainly instead of paraphrasing. Replace with the Azure chat model
    adapter (see app/rag/chain.build_azure_chain) once Foundry is wired up."""

    def generate(self, system: str, user: str) -> str:
        lines = [ln for ln in user.split("\n") if ln.strip().startswith("-")]
        if not lines:
            return "Not found in source."
        return " ".join(line.strip("- ").strip() for line in lines)


def explain_supplier(db: Session, supplier_id: str, criterion: str) -> dict:
    if settings.azure_rag_enabled:
        try:
            retriever, llm = build_azure_chain()
        except Exception as exc:  # pragma: no cover - runtime resilience for Azure auth/network issues
            logger.warning("Azure RAG unavailable, falling back to local retriever: %s", exc)
            retriever = _DbKeywordRetriever(db)
            llm = _EchoLLM()
    else:
        retriever = _DbKeywordRetriever(db)
        llm = _EchoLLM()
    return explain(retriever, llm, supplier_id, criterion)
