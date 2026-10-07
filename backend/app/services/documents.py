"""Store an uploaded file as searchable chunks."""

from __future__ import annotations

import logging

from sqlalchemy.orm import Session

from app.core.config import Settings
from app.core.errors import AppError
from app.models import Chunk, Document
from app.services.embeddings.bedrock import BedrockEmbedder
from app.services.ingestion.chunk import chunk_blocks
from app.services.ingestion.extract import extract_document
from app.services.uploads import UploadPayload

logger = logging.getLogger(__name__)


def ingest_document(
    db: Session,
    payload: UploadPayload,
    embedder: BedrockEmbedder,
    settings: Settings,
) -> Document:
    document = Document(
        filename=payload.filename,
        media_type=payload.media_type,
        status="processing",
        chunk_count=0,
    )
    db.add(document)
    db.commit()
    db.refresh(document)

    try:
        blocks = extract_document(payload.filename, payload.data)
        drafts = chunk_blocks(
            blocks,
            max_chars=settings.chunk_max_chars,
            overlap=settings.chunk_overlap_chars,
        )
        if not drafts:
            raise AppError(
                "No text could be extracted from that file. Scanned PDFs are not supported.",
                422,
            )
        vectors = embedder.embed_texts([draft.content for draft in drafts])
        if len(vectors) != len(drafts):
            raise AppError("The embedding service returned an unexpected result.", 502)
        for draft, vector in zip(drafts, vectors, strict=True):
            db.add(
                Chunk(
                    document_id=document.id,
                    chunk_index=draft.chunk_index,
                    content=draft.content,
                    page_start=draft.page_start,
                    page_end=draft.page_end,
                    section_title=draft.section_title,
                    embedding=vector,
                )
            )
        document.status = "ready"
        document.chunk_count = len(drafts)
        document.error_message = None
        db.commit()
        db.refresh(document)
        logger.info("Indexed %s chunks for document %s", document.chunk_count, document.id)
        return document
    except Exception as exc:
        db.rollback()
        failed = db.get(Document, document.id)
        message = exc.message if isinstance(exc, AppError) else "The document could not be indexed."
        if failed is not None:
            failed.status = "failed"
            failed.error_message = message
            db.commit()
        if isinstance(exc, AppError):
            raise
        logger.exception("Document indexing failed")
        raise AppError(message, 500) from exc
