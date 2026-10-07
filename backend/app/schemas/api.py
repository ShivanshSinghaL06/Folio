import uuid
from datetime import datetime

from pydantic import BaseModel, Field, field_validator


class DocumentOut(BaseModel):
    id: uuid.UUID
    filename: str
    media_type: str
    status: str
    error_message: str | None
    chunk_count: int
    created_at: datetime

    model_config = {"from_attributes": True}


class CitationOut(BaseModel):
    index: int
    document_id: uuid.UUID
    document_name: str
    page_start: int | None = None
    page_end: int | None = None
    section_title: str | None = None
    excerpt: str
    cited_inline: bool


class MessageOut(BaseModel):
    id: uuid.UUID
    role: str
    content: str
    citations: list[CitationOut]
    created_at: datetime

    model_config = {"from_attributes": True}


class ConversationOut(BaseModel):
    id: uuid.UUID
    title: str
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}


class ConversationDetail(ConversationOut):
    messages: list[MessageOut]


class ConversationCreate(BaseModel):
    title: str | None = None


class AskRequest(BaseModel):
    content: str = Field(min_length=1, max_length=4000)
    document_ids: list[uuid.UUID] | None = None

    @field_validator("content")
    @classmethod
    def not_blank(cls, value: str) -> str:
        cleaned = " ".join(value.split())
        if not cleaned:
            raise ValueError("Question is empty")
        return cleaned


class AskResponse(BaseModel):
    user_message: MessageOut
    assistant_message: MessageOut


class SearchRequest(BaseModel):
    query: str = Field(min_length=1, max_length=4000)
    document_ids: list[uuid.UUID] | None = None

    @field_validator("query")
    @classmethod
    def not_blank(cls, value: str) -> str:
        cleaned = " ".join(value.split())
        if not cleaned:
            raise ValueError("Question is empty")
        return cleaned


class SearchHit(BaseModel):
    chunk_id: uuid.UUID
    document_id: uuid.UUID
    document_name: str
    content: str
    page_start: int | None
    page_end: int | None
    section_title: str | None
    lexical_score: float | None
    vector_score: float | None
    fusion_score: float | None
    rerank_score: float | None
