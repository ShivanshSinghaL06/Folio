"""Conversation persistence around the answering pipeline."""

from __future__ import annotations

import uuid
from datetime import datetime, timedelta, timezone

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.core.config import Settings
from app.core.errors import AppError
from app.models import Conversation, Message
from app.services.answering import compose_answer
from app.services.retrieval.pipeline import prepare_query


def create_conversation(db: Session, title: str | None) -> Conversation:
    cleaned = " ".join((title or "").split())
    conversation = Conversation(title=cleaned[:200] or "New chat")
    db.add(conversation)
    db.commit()
    db.refresh(conversation)
    return conversation


def list_conversations(db: Session) -> list[Conversation]:
    stmt = select(Conversation).order_by(Conversation.updated_at.desc(), Conversation.created_at.desc())
    return list(db.scalars(stmt).all())


def get_conversation(db: Session, conversation_id: uuid.UUID) -> Conversation:
    conversation = db.get(Conversation, conversation_id)
    if conversation is None:
        raise AppError("Conversation not found.", 404)
    return conversation


def list_messages(db: Session, conversation_id: uuid.UUID) -> list[Message]:
    get_conversation(db, conversation_id)
    stmt = (
        select(Message)
        .where(Message.conversation_id == conversation_id)
        .order_by(Message.created_at, Message.id)
    )
    return list(db.scalars(stmt).all())


def delete_conversation(db: Session, conversation_id: uuid.UUID) -> None:
    conversation = get_conversation(db, conversation_id)
    db.delete(conversation)
    db.commit()


def ask_question(
    db: Session,
    conversation_id: uuid.UUID,
    content: str,
    document_ids: list[uuid.UUID] | None,
    *,
    embedder,
    lexical,
    vector,
    reranker,
    generator,
    settings: Settings,
) -> tuple[Message, Message]:
    conversation = get_conversation(db, conversation_id)
    prepared = prepare_query(content, settings.max_query_chars)
    history = [(message.role, message.content) for message in list_messages(db, conversation_id)]
    history = [(role, text) for role, text in history if role in {"user", "assistant"}]

    try:
        result = compose_answer(
            db,
            prepared,
            history,
            document_ids=document_ids,
            embedder=embedder,
            lexical=lexical,
            vector=vector,
            reranker=reranker,
            generator=generator,
            settings=settings,
        )
        now = datetime.now(timezone.utc)
        user_message = Message(
            conversation_id=conversation.id,
            role="user",
            content=prepared,
            citations=[],
            created_at=now,
        )
        assistant_message = Message(
            conversation_id=conversation.id,
            role="assistant",
            content=result.text,
            citations=[citation.as_dict() for citation in result.citations],
            created_at=now + timedelta(milliseconds=1),
        )
        if conversation.title == "New chat":
            conversation.title = prepared[:80]
        conversation.updated_at = now
        db.add(user_message)
        db.add(assistant_message)
        db.commit()
        db.refresh(user_message)
        db.refresh(assistant_message)
        return user_message, assistant_message
    except Exception:
        db.rollback()
        raise
