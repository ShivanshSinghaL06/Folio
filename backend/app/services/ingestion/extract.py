"""Extract readable text from PDF and Word files."""

from __future__ import annotations

from io import BytesIO
from pathlib import Path

from docx import Document
from docx.oxml.ns import qn
from docx.table import Table
from docx.text.paragraph import Paragraph
from pypdf import PdfReader

from app.core.errors import AppError
from app.services.ingestion.types import TextBlock


def extract_document(filename: str, data: bytes) -> list[TextBlock]:
    suffix = Path(filename).suffix.lower()
    try:
        if suffix == ".pdf":
            return _extract_pdf(data)
        if suffix == ".docx":
            return _extract_docx(data)
    except AppError:
        raise
    except Exception as exc:
        raise AppError("The file could not be read.", 400) from exc
    raise AppError("Upload a PDF or Word (.docx) file.", 400)


def _extract_pdf(data: bytes) -> list[TextBlock]:
    reader = PdfReader(BytesIO(data))
    blocks: list[TextBlock] = []
    for index, page in enumerate(reader.pages, start=1):
        cleaned = _clean(page.extract_text() or "")
        if cleaned:
            blocks.append(TextBlock(text=cleaned, page=index, section=None))
    return blocks


def _extract_docx(data: bytes) -> list[TextBlock]:
    document = Document(BytesIO(data))
    blocks: list[TextBlock] = []
    section: str | None = None
    for item in _iter_blocks(document):
        if isinstance(item, Paragraph):
            cleaned = _clean(item.text)
            if not cleaned:
                continue
            if _is_heading(item):
                section = cleaned[:512]
                blocks.append(TextBlock(text=cleaned, page=None, section=section))
                continue
            blocks.append(TextBlock(text=cleaned, page=None, section=section))
            continue
        for row in item.rows:
            cells = [_clean(cell.text) for cell in row.cells]
            row_text = " | ".join(cell for cell in cells if cell)
            if row_text:
                blocks.append(TextBlock(text=row_text, page=None, section=section))
    return blocks


def _iter_blocks(document: Document):
    parent = document
    for child in document.element.body.iterchildren():
        if child.tag == qn("w:p"):
            yield Paragraph(child, parent)
        elif child.tag == qn("w:tbl"):
            yield Table(child, parent)


def _is_heading(paragraph: Paragraph) -> bool:
    style = paragraph.style.name if paragraph.style is not None else ""
    return style.lower().startswith("heading")


def _clean(text: str) -> str:
    without_nulls = text.replace("\x00", " ")
    lines = [" ".join(line.split()) for line in without_nulls.splitlines()]
    return "\n".join(line for line in lines if line).strip()
