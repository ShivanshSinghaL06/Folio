from dataclasses import dataclass, replace


@dataclass
class RetrievedChunk:
    chunk_id: str
    document_id: str
    document_name: str
    content: str
    page_start: int | None = None
    page_end: int | None = None
    section_title: str | None = None
    vector_score: float | None = None
    lexical_score: float | None = None
    fusion_score: float | None = None
    rerank_score: float | None = None


def merge_hit(existing: RetrievedChunk, incoming: RetrievedChunk) -> RetrievedChunk:
    return replace(
        existing,
        vector_score=incoming.vector_score if incoming.vector_score is not None else existing.vector_score,
        lexical_score=incoming.lexical_score if incoming.lexical_score is not None else existing.lexical_score,
        document_name=incoming.document_name or existing.document_name,
        content=incoming.content or existing.content,
        page_start=incoming.page_start if incoming.page_start is not None else existing.page_start,
        page_end=incoming.page_end if incoming.page_end is not None else existing.page_end,
        section_title=incoming.section_title if incoming.section_title is not None else existing.section_title,
    )
