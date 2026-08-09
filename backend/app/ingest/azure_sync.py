from __future__ import annotations

import logging
from typing import Any, Iterable

from azure.core.credentials import AzureKeyCredential
from azure.core.exceptions import ResourceNotFoundError
from azure.identity import DefaultAzureCredential
from azure.search.documents import SearchClient
from azure.search.documents.indexes import SearchIndexClient
from azure.search.documents.indexes.models import (
    HnswAlgorithmConfiguration,
    SearchField,
    SearchFieldDataType,
    SearchIndex,
    SimpleField,
    VectorSearch,
    VectorSearchProfile,
)
from app.config import settings
from app.models import EvidenceChunk

logger = logging.getLogger(__name__)


def _search_client() -> SearchClient:
    if not settings.azure_search_endpoint:
        raise ValueError("Azure search endpoint is not configured.")

    credential = (
        AzureKeyCredential(settings.azure_search_api_key)
        if settings.azure_search_api_key
        else DefaultAzureCredential()
    )
    return SearchClient(
        endpoint=settings.azure_search_endpoint,
        index_name=settings.azure_search_index_name,
        credential=credential,
    )


def _index_client() -> SearchIndexClient:
    if not settings.azure_search_endpoint:
        raise ValueError("Azure search endpoint is not configured.")

    credential = (
        AzureKeyCredential(settings.azure_search_api_key)
        if settings.azure_search_api_key
        else DefaultAzureCredential()
    )
    return SearchIndexClient(endpoint=settings.azure_search_endpoint, credential=credential)


def _normalize_azure_openai_endpoint(endpoint: str) -> str:
    stripped = endpoint.rstrip("/")
    for suffix in ("/openai/v1", "/openai/v1/responses"):
        if stripped.endswith(suffix):
            return stripped[: -len(suffix)]
    return stripped


def _build_embedding_model() -> Any:
    if settings.azure_openai_endpoint and settings.azure_openai_api_key:
        from langchain_openai import AzureOpenAIEmbeddings

        return AzureOpenAIEmbeddings(
            azure_endpoint=_normalize_azure_openai_endpoint(settings.azure_openai_endpoint),
            api_key=settings.azure_openai_api_key,
            api_version=settings.azure_openai_api_version,
            deployment=settings.azure_embedding_deployment,
        )

    if not settings.azure_ai_project_endpoint:
        raise ValueError("Azure AI project endpoint or Azure OpenAI endpoint is not configured.")
    from langchain_azure_ai.embeddings import AzureAIOpenAIApiEmbeddingsModel

    credential = DefaultAzureCredential()
    return AzureAIOpenAIApiEmbeddingsModel(
        project_endpoint=settings.azure_ai_project_endpoint,
        credential=credential,
        model=settings.azure_embedding_deployment,
    )


def _ensure_search_index() -> None:
    index_client = _index_client()
    index_name = settings.azure_search_index_name
    try:
        existing_index = index_client.get_index(index_name)
    except ResourceNotFoundError:
        existing_index = None

    if existing_index is not None:
        field_names = {field.name for field in existing_index.fields}
        if "content_vector" in field_names and any(
            getattr(field, "name", None) == "content_vector" and getattr(field, "searchable", False)
            for field in existing_index.fields
        ):
            logger.info("Azure Search index %s already exists with vector fields", index_name)
            return

    fields = [
        SimpleField(name="chunk_id", type=SearchFieldDataType.STRING, key=True, filterable=True),
        SimpleField(name="supplier_id", type=SearchFieldDataType.STRING, filterable=True),
        SimpleField(name="doc_id", type=SearchFieldDataType.STRING, filterable=True),
        SimpleField(name="source_field", type=SearchFieldDataType.STRING, filterable=True),
        SearchField(name="content", type=SearchFieldDataType.STRING, searchable=True),
        SearchField(
            name="content_vector",
            type=SearchFieldDataType.Collection(SearchFieldDataType.SINGLE),
            searchable=True,
            vector_search_dimensions=3072,
            vector_search_profile_name="default-profile",
        ),
    ]
    vector_search = VectorSearch(
        profiles=[VectorSearchProfile(name="default-profile", algorithm_configuration_name="default-hnsw")],
        algorithms=[HnswAlgorithmConfiguration(name="default-hnsw")],
    )
    index = SearchIndex(name=index_name, fields=fields, vector_search=vector_search)

    if existing_index is not None:
        try:
            index_client.delete_index(index_name)
        except Exception as exc:  # pragma: no cover - resilience when deleting an index is not possible
            logger.warning("Azure Search index %s could not be deleted before recreation: %s", index_name, exc)

    index_client.create_or_update_index(index)
    logger.info("Azure Search index %s created or recreated", index_name)


def sync_evidence_chunks(chunks: Iterable[EvidenceChunk]) -> int:
    if not settings.azure_search_endpoint or not settings.azure_ai_project_endpoint:
        raise ValueError("Azure search and AI endpoints must be configured to sync evidence chunks.")

    try:
        _ensure_search_index()
        search_client = _search_client()
        embedding_model = _build_embedding_model()
        contents = [chunk.content for chunk in chunks]
        vectors = embedding_model.embed_documents(contents)
        documents = []
        for chunk, vector in zip(chunks, vectors):
            documents.append(
                {
                    "chunk_id": f"{chunk.supplier_id}-{chunk.doc_id}-{chunk.source_field}",
                    "supplier_id": chunk.supplier_id,
                    "doc_id": chunk.doc_id,
                    "source_field": chunk.source_field,
                    "content": chunk.content,
                    "content_vector": vector,
                }
            )

        results = search_client.upload_documents(documents)
        failed = [r for r in results if not getattr(r, "succeeded", False)]
        if failed:
            raise RuntimeError(
                f"Failed to upload {len(failed)} evidence chunks to Azure Search: {failed}"
            )
        return len(results)
    except Exception as exc:  # pragma: no cover - runtime resilience for Azure auth/network issues
        logger.warning("Azure Search sync skipped: %s", exc)
        return 0
