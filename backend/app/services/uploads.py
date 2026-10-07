"""Upload checks that do not need the database."""

from dataclasses import dataclass
from pathlib import Path

from app.core.errors import AppError

ALLOWED_SUFFIXES = {".pdf", ".docx"}
MEDIA_TYPES = {
    ".pdf": "application/pdf",
    ".docx": "application/vnd.openxmlformats-officedocument.wordprocessingml.document",
}


@dataclass(frozen=True)
class UploadPayload:
    filename: str
    data: bytes

    @property
    def media_type(self) -> str:
        return MEDIA_TYPES[Path(self.filename).suffix.lower()]


def validate_upload(filename: str, data: bytes, max_bytes: int) -> UploadPayload:
    cleaned = Path(filename or "").name.strip()
    if not cleaned or cleaned in {".", ".."}:
        raise AppError("A file name is required.", 400)
    suffix = Path(cleaned).suffix.lower()
    if suffix not in ALLOWED_SUFFIXES:
        raise AppError("Upload a PDF or Word (.docx) file.", 400)
    if not data:
        raise AppError("The file is empty.", 400)
    if len(data) > max_bytes:
        raise AppError("The file is larger than the upload limit.", 413)
    return UploadPayload(filename=cleaned, data=data)
