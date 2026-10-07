"""Turn retrieved chunks into citation records and note which markers the answer used."""

from __future__ import annotations

import re
from dataclasses import dataclass

from app.services.retrieval.types import RetrievedChunk

_MARKER = re.compile(r"\[(\d+)\]")
_EXCERPT_CHARS = 320


@dataclass(frozen=True)
class Citation:
    index: int
    document_id: str
    document_name: str
    page_start: int | None
    page_end: int | None
    section_title: str | None
    excerpt: str
    cited_inline: bool

    def as_dict(self) -> dict:
        return {
            "index": self.index,
            "document_id": self.document_id,
            "document_name": self.document_name,
            "page_start": self.page_start,
            "page_end": self.page_end,
            "section_title": self.section_title,
            "excerpt": self.excerpt,
            "cited_inline": self.cited_inline,
        }


def inline_citation_indexes(answer: str) -> list[int]:
    seen: list[int] = []
    for match in _MARKER.finditer(answer):
        number = int(match.group(1))
        if number not in seen:
            seen.append(number)
    return seen


def build_citations(chunks: list[RetrievedChunk], answer: str) -> list[Citation]:
    used = set(inline_citation_indexes(answer))
    citations: list[Citation] = []
    for index, chunk in enumerate(chunks, start=1):
        citations.append(
            Citation(
                index=index,
                document_id=chunk.document_id,
                document_name=chunk.document_name,
                page_start=chunk.page_start,
                page_end=chunk.page_end,
                section_title=chunk.section_title,
                excerpt=_excerpt(chunk.content),
                cited_inline=index in used,
            )
        )
    return citations


def _excerpt(content: str) -> str:
    compact = " ".join(content.split())
    if len(compact) <= _EXCERPT_CHARS:
        return compact
    return compact[: _EXCERPT_CHARS - 1] + "…"
