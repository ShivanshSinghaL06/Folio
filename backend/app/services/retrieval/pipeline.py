"""Fuse lexical and vector hit lists, then rerank."""

from __future__ import annotations

from typing import Protocol

from app.core.config import Settings
from app.core.errors import AppError
from app.services.retrieval.fusion import reciprocal_rank_fusion
from app.services.retrieval.types import RetrievedChunk, merge_hit


class QueryEmbedder(Protocol):
    def embed_query(self, text: str) -> list[float]: ...


class HitSource(Protocol):
    def search(self, db, query, *, limit: int, document_ids) -> list[RetrievedChunk]: ...


class VectorSource(Protocol):
    def search(self, db, embedding: list[float], *, limit: int, document_ids) -> list[RetrievedChunk]: ...


class Reranker(Protocol):
    def rerank(self, query: str, candidates: list[RetrievedChunk], limit: int) -> list[RetrievedChunk]: ...


def prepare_query(text: str, max_length: int) -> str:
    cleaned = " ".join(text.split())
    if not cleaned:
        raise AppError("Question is empty.", 400)
    if len(cleaned) > max_length:
        raise AppError("Question is too long.", 400)
    return cleaned


def fuse_hits(
    lexical_hits: list[RetrievedChunk],
    vector_hits: list[RetrievedChunk],
    *,
    k: int,
    limit: int,
) -> list[RetrievedChunk]:
    by_id: dict[str, RetrievedChunk] = {}
    for hit in [*lexical_hits, *vector_hits]:
        current = by_id.get(hit.chunk_id)
        by_id[hit.chunk_id] = hit if current is None else merge_hit(current, hit)

    fused: list[RetrievedChunk] = []
    ranking = reciprocal_rank_fusion(
        [
            [hit.chunk_id for hit in lexical_hits],
            [hit.chunk_id for hit in vector_hits],
        ],
        k=k,
    )
    for chunk_id, score in ranking[:limit]:
        fused.append(replace_score(by_id[chunk_id], score))
    return fused


def replace_score(hit: RetrievedChunk, fusion_score: float) -> RetrievedChunk:
    from dataclasses import replace

    return replace(hit, fusion_score=fusion_score)


def run_retrieval(
    db,
    query: str,
    *,
    embedder: QueryEmbedder,
    lexical: HitSource,
    vector: VectorSource,
    reranker: Reranker,
    settings: Settings,
    document_ids,
) -> list[RetrievedChunk]:
    prepared = prepare_query(query, settings.max_query_chars)
    embedding = embedder.embed_query(prepared)
    lexical_hits = lexical.search(
        db,
        prepared,
        limit=settings.retrieval_candidates,
        document_ids=document_ids,
    )
    vector_hits = vector.search(
        db,
        embedding,
        limit=settings.retrieval_candidates,
        document_ids=document_ids,
    )
    fused = fuse_hits(
        lexical_hits,
        vector_hits,
        k=settings.rrf_k,
        limit=settings.retrieval_candidates,
    )
    return reranker.rerank(prepared, fused, limit=settings.rerank_top_k)
