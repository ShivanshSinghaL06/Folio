import uuid

from fastapi import APIRouter, Depends, status
from sqlalchemy.orm import Session

from app.api.deps import Services, get_db, get_services
from app.schemas.api import (
    AskRequest,
    AskResponse,
    ConversationCreate,
    ConversationDetail,
    ConversationOut,
    MessageOut,
)
from app.services.conversations import (
    ask_question,
    create_conversation,
    delete_conversation,
    get_conversation,
    list_conversations,
    list_messages,
)

router = APIRouter(prefix="/conversations", tags=["conversations"])


@router.get("", response_model=list[ConversationOut])
def list_all(db: Session = Depends(get_db)):
    return list_conversations(db)


@router.post("", response_model=ConversationOut, status_code=status.HTTP_201_CREATED)
def create(body: ConversationCreate, db: Session = Depends(get_db)):
    return create_conversation(db, body.title)


@router.get("/{conversation_id}", response_model=ConversationDetail)
def read(conversation_id: uuid.UUID, db: Session = Depends(get_db)):
    conversation = get_conversation(db, conversation_id)
    messages = list_messages(db, conversation_id)
    return ConversationDetail(
        id=conversation.id,
        title=conversation.title,
        created_at=conversation.created_at,
        updated_at=conversation.updated_at,
        messages=[MessageOut.model_validate(message) for message in messages],
    )


@router.delete("/{conversation_id}", status_code=status.HTTP_204_NO_CONTENT)
def remove(conversation_id: uuid.UUID, db: Session = Depends(get_db)) -> None:
    delete_conversation(db, conversation_id)


@router.post("/{conversation_id}/messages", response_model=AskResponse)
def ask(
    conversation_id: uuid.UUID,
    body: AskRequest,
    db: Session = Depends(get_db),
    services: Services = Depends(get_services),
):
    user_message, assistant_message = ask_question(
        db,
        conversation_id,
        body.content,
        body.document_ids,
        embedder=services.embedder,
        lexical=services.lexical,
        vector=services.vector,
        reranker=services.reranker,
        generator=services.generator,
        settings=services.settings,
    )
    return AskResponse(
        user_message=MessageOut.model_validate(user_message),
        assistant_message=MessageOut.model_validate(assistant_message),
    )
