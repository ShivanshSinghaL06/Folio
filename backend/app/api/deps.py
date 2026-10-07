from dataclasses import dataclass

from fastapi import Request
from sqlalchemy.orm import Session

from app.core.config import Settings, get_settings
from app.db.session import get_db
from app.services.embeddings.bedrock import BedrockEmbedder
from app.services.generation.bedrock import BedrockGenerator
from app.services.retrieval.lexical import LexicalSearch
from app.services.retrieval.vector import VectorSearch


@dataclass
class Services:
    settings: Settings
    embedder: BedrockEmbedder
    generator: BedrockGenerator
    reranker: object
    lexical: LexicalSearch
    vector: VectorSearch


def get_services(request: Request) -> Services:
    return request.app.state.services


__all__ = ["Services", "get_db", "get_services", "get_settings", "Session"]
