"""Retrieval plus grounded generation, independent of HTTP."""

from __future__ import annotations

import uuid
from dataclasses import dataclass

from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.core.config import Settings
from app.core.errors import AppError
from app.models import Document
from app.services.generation.citations import Citation, build_citations
from app.services.generation.prompt import trim_history
from app.services.retrieval.pipeline import run_retrieval
from app.services.retrieval.types import RetrievedChunk

NO_MATCH_ANSWER = "I couldn't find relevant passages in the uploaded documents for that question."


@dataclass(frozen=True)
class AnswerResult:
    text: str
    citations: list[Citation]
    chunks: list[RetrievedChunk]


def assert_documents_ready(db: Session, document_ids: list[uuid.UUID] | None) -> None:
    if not document_ids:
        ready = db.scalar(select(func.count()).select_from(Document).where(Document.status == "ready"))
        if not ready:
            raise AppError("Upload a document before asking a question.", 409)
        return

    rows = list(db.scalars(select(Document).where(Document.id.in_(document_ids))).all())
    found = {row.id for row in rows}
    if any(document_id not in found for document_id in document_ids):
        raise AppError("One or more documents were not found.", 404)
    if any(row.status != "ready" for row in rows):
        raise AppError("Selected documents are not ready for search.", 409)


def search_documents(
    db: Session,
    query: str,
    *,
    document_ids: list[uuid.UUID] | None,
    embedder,
    lexical,
    vector,
    reranker,
    settings: Settings,
) -> list[RetrievedChunk]:
    assert_documents_ready(db, document_ids)
    return run_retrieval(
        db,
        query,
        embedder=embedder,
        lexical=lexical,
        vector=vector,
        reranker=reranker,
        settings=settings,
        document_ids=document_ids,
    )


def compose_answer(
    db: Session,
    query: str,
    history: list[tuple[str, str]],
    *,
    document_ids: list[uuid.UUID] | None,
    embedder,
    lexical,
    vector,
    reranker,
    generator,
    settings: Settings,
) -> AnswerResult:
    chunks = search_documents(
        db,
        query,
        document_ids=document_ids,
        embedder=embedder,
        lexical=lexical,
        vector=vector,
        reranker=reranker,
        settings=settings,
    )
    if not chunks:
        return AnswerResult(text=NO_MATCH_ANSWER, citations=[], chunks=[])
    bounded_history = trim_history(history, settings.chat_history_messages)
    raw = generator.generate(query=query, chunks=chunks, history=bounded_history)
    return AnswerResult(text=raw, citations=build_citations(chunks, raw), chunks=chunks)
