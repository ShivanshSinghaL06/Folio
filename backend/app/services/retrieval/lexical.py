"""PostgreSQL full-text candidates rescored with Okapi BM25."""

from __future__ import annotations

import uuid

from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.models import Chunk, Document
from app.services.retrieval.bm25 import bm25_scores
from app.services.retrieval.tokenize import tokenize
from app.services.retrieval.types import RetrievedChunk


class LexicalSearch:
    def search(
        self,
        db: Session,
        query: str,
        *,
        limit: int,
        document_ids: list[uuid.UUID] | None,
    ) -> list[RetrievedChunk]:
        terms = list(dict.fromkeys(tokenize(query)))
        if not terms:
            return []

        candidate_limit = max(limit * 5, 50)
        rows = db.execute(_candidate_query(query, candidate_limit, document_ids)).all()
        if not rows:
            return []

        document_count, average_length = _corpus_stats(db, document_ids)
        documents = [(str(row.id), row.content) for row in rows]
        if document_count <= 0:
            document_count = len(documents)
        if average_length <= 0:
            lengths = [max(len(tokenize(text)), 1) for _doc_id, text in documents]
            average_length = sum(lengths) / len(lengths)
        frequencies = {term: _document_frequency(db, term, document_ids) for term in terms}
        ranked = bm25_scores(
            query,
            documents,
            document_count=document_count,
            document_frequencies=frequencies,
            average_document_length=average_length or 1.0,
        )
        by_id = {str(row.id): row for row in rows}
        hits: list[RetrievedChunk] = []
        for chunk_id, score in ranked:
            if score <= 0:
                continue
            row = by_id[chunk_id]
            hits.append(_to_chunk(row, lexical_score=score))
            if len(hits) >= limit:
                break
        return hits


def _candidate_query(query: str, limit: int, document_ids: list[uuid.UUID] | None):
    tsquery = func.plainto_tsquery("english", query)
    rank = func.ts_rank_cd(Chunk.search_vector, tsquery)
    stmt = (
        select(
            Chunk.id,
            Chunk.document_id,
            Document.filename,
            Chunk.content,
            Chunk.page_start,
            Chunk.page_end,
            Chunk.section_title,
        )
        .join(Document, Document.id == Chunk.document_id)
        .where(Document.status == "ready", Chunk.search_vector.op("@@")(tsquery))
        .order_by(rank.desc())
        .limit(limit)
    )
    if document_ids:
        stmt = stmt.where(Chunk.document_id.in_(document_ids))
    return stmt


def _corpus_stats(db: Session, document_ids: list[uuid.UUID] | None) -> tuple[int, float]:
    token_count = func.cardinality(func.regexp_split_to_array(func.btrim(Chunk.content), r"\s+"))
    stmt = (
        select(func.count(), func.avg(token_count))
        .select_from(Chunk)
        .join(Document, Document.id == Chunk.document_id)
        .where(Document.status == "ready")
    )
    if document_ids:
        stmt = stmt.where(Chunk.document_id.in_(document_ids))
    count, average = db.execute(stmt).one()
    return int(count or 0), float(average or 0.0)


def _document_frequency(db: Session, term: str, document_ids: list[uuid.UUID] | None) -> int:
    tsquery = func.plainto_tsquery("english", term)
    stmt = (
        select(func.count())
        .select_from(Chunk)
        .join(Document, Document.id == Chunk.document_id)
        .where(Document.status == "ready", Chunk.search_vector.op("@@")(tsquery))
    )
    if document_ids:
        stmt = stmt.where(Chunk.document_id.in_(document_ids))
    return int(db.scalar(stmt) or 0)


def _to_chunk(row, *, lexical_score: float) -> RetrievedChunk:
    return RetrievedChunk(
        chunk_id=str(row.id),
        document_id=str(row.document_id),
        document_name=row.filename,
        content=row.content,
        page_start=row.page_start,
        page_end=row.page_end,
        section_title=row.section_title,
        lexical_score=lexical_score,
    )
