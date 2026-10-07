"""pgvector cosine search."""

from __future__ import annotations

import uuid

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models import Chunk, Document
from app.services.retrieval.types import RetrievedChunk


class VectorSearch:
    def search(
        self,
        db: Session,
        embedding: list[float],
        *,
        limit: int,
        document_ids: list[uuid.UUID] | None,
    ) -> list[RetrievedChunk]:
        distance = Chunk.embedding.cosine_distance(embedding)
        score = (1 - distance).label("vector_score")
        stmt = (
            select(
                Chunk.id,
                Chunk.document_id,
                Document.filename,
                Chunk.content,
                Chunk.page_start,
                Chunk.page_end,
                Chunk.section_title,
                score,
            )
            .join(Document, Document.id == Chunk.document_id)
            .where(Document.status == "ready")
            .order_by(distance)
            .limit(limit)
        )
        if document_ids:
            stmt = stmt.where(Chunk.document_id.in_(document_ids))
        rows = db.execute(stmt).all()
        return [
            RetrievedChunk(
                chunk_id=str(row.id),
                document_id=str(row.document_id),
                document_name=row.filename,
                content=row.content,
                page_start=row.page_start,
                page_end=row.page_end,
                section_title=row.section_title,
                vector_score=float(row.vector_score),
            )
            for row in rows
        ]
