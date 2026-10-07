import uuid

from fastapi import APIRouter, Depends, File, UploadFile, status
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.api.deps import Services, get_db, get_services
from app.core.errors import AppError
from app.models import Document
from app.schemas.api import DocumentOut
from app.services.documents import ingest_document
from app.services.uploads import validate_upload

router = APIRouter(prefix="/documents", tags=["documents"])


@router.get("", response_model=list[DocumentOut])
def list_documents(db: Session = Depends(get_db)) -> list[Document]:
    stmt = select(Document).order_by(Document.created_at.desc())
    return list(db.scalars(stmt).all())


@router.post("", response_model=DocumentOut, status_code=status.HTTP_201_CREATED)
def upload_document(
    file: UploadFile = File(...),
    db: Session = Depends(get_db),
    services: Services = Depends(get_services),
) -> Document:
    payload = validate_upload(file.filename or "", file.file.read(), services.settings.max_upload_bytes)
    return ingest_document(db, payload, services.embedder, services.settings)


@router.get("/{document_id}", response_model=DocumentOut)
def get_document(document_id: uuid.UUID, db: Session = Depends(get_db)) -> Document:
    document = db.get(Document, document_id)
    if document is None:
        raise AppError("Document not found.", 404)
    return document


@router.delete("/{document_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_document(document_id: uuid.UUID, db: Session = Depends(get_db)) -> None:
    document = db.get(Document, document_id)
    if document is None:
        raise AppError("Document not found.", 404)
    db.delete(document)
    db.commit()
