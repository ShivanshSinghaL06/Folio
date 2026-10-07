from dataclasses import dataclass


@dataclass(frozen=True)
class TextBlock:
    text: str
    page: int | None = None
    section: str | None = None


@dataclass(frozen=True)
class ChunkDraft:
    content: str
    page_start: int | None
    page_end: int | None
    section_title: str | None
    chunk_index: int
