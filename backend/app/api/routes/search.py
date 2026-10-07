from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.api.deps import Services, get_db, get_services
from app.schemas.api import SearchHit, SearchRequest
from app.services.answering import search_documents

router = APIRouter(prefix="/search", tags=["search"])


@router.post("", response_model=list[SearchHit])
def search(
    body: SearchRequest,
    db: Session = Depends(get_db),
    services: Services = Depends(get_services),
) -> list[SearchHit]:
    chunks = search_documents(
        db,
        body.query,
        document_ids=body.document_ids,
        embedder=services.embedder,
        lexical=services.lexical,
        vector=services.vector,
        reranker=services.reranker,
        settings=services.settings,
    )
    return [
        SearchHit(
            chunk_id=chunk.chunk_id,
            document_id=chunk.document_id,
            document_name=chunk.document_name,
            content=chunk.content,
            page_start=chunk.page_start,
            page_end=chunk.page_end,
            section_title=chunk.section_title,
            lexical_score=chunk.lexical_score,
            vector_score=chunk.vector_score,
            fusion_score=chunk.fusion_score,
            rerank_score=chunk.rerank_score,
        )
        for chunk in chunks
    ]
