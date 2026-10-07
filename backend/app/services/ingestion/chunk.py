"""Split extracted blocks into overlapping chunks that keep page and section labels."""

from app.services.ingestion.types import ChunkDraft, TextBlock


def chunk_blocks(blocks: list[TextBlock], *, max_chars: int = 1200, overlap: int = 200) -> list[ChunkDraft]:
    if max_chars < 200:
        raise ValueError("max_chars is too small")
    if overlap < 0 or overlap >= max_chars:
        raise ValueError("overlap must be smaller than max_chars")

    pieces: list[TextBlock] = []
    for block in blocks:
        for part in _split_text(block.text, max_chars):
            pieces.append(TextBlock(text=part, page=block.page, section=block.section))

    groups: list[list[TextBlock]] = []
    current: list[TextBlock] = []
    current_len = 0
    for piece in pieces:
        needed = current_len + (1 if current else 0) + len(piece.text)
        if current and needed > max_chars:
            groups.append(current)
            current = _overlap_tail(current, overlap)
            current_len = _joined_len(current)
            if current and current_len + 1 + len(piece.text) > max_chars:
                current = []
                current_len = 0
            needed = current_len + (1 if current else 0) + len(piece.text)
        current.append(piece)
        current_len = needed

    if current:
        groups.append(current)

    drafts: list[ChunkDraft] = []
    for index, group in enumerate(groups):
        pages = [piece.page for piece in group if piece.page is not None]
        section = next((piece.section for piece in group if piece.section), None)
        drafts.append(
            ChunkDraft(
                content="\n".join(piece.text for piece in group),
                page_start=min(pages) if pages else None,
                page_end=max(pages) if pages else None,
                section_title=section,
                chunk_index=index,
            )
        )
    return drafts


def _split_text(text: str, max_chars: int) -> list[str]:
    cleaned = " ".join(text.split())
    if not cleaned:
        return []
    if len(cleaned) <= max_chars:
        return [cleaned]

    parts: list[str] = []
    start = 0
    while start < len(cleaned):
        end = min(start + max_chars, len(cleaned))
        if end < len(cleaned):
            split_at = cleaned.rfind(" ", start, end)
            if split_at <= start:
                split_at = end
            end = split_at
        piece = cleaned[start:end].strip()
        if piece:
            parts.append(piece)
        if end <= start:
            end = start + 1
        start = end
        while start < len(cleaned) and cleaned[start] == " ":
            start += 1
    return parts


def _overlap_tail(pieces: list[TextBlock], overlap: int) -> list[TextBlock]:
    if overlap == 0:
        return []
    chosen: list[TextBlock] = []
    total = 0
    for piece in reversed(pieces):
        extra = len(piece.text) + (1 if chosen else 0)
        if not chosen and len(piece.text) > overlap:
            break
        if chosen and total + extra > overlap:
            break
        chosen.append(piece)
        total += extra
    chosen.reverse()
    return chosen


def _joined_len(pieces: list[TextBlock]) -> int:
    if not pieces:
        return 0
    return sum(len(piece.text) for piece in pieces) + (len(pieces) - 1)
