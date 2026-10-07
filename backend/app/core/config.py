"""Application configuration. Values come from the environment or a local .env file."""

from functools import lru_cache

from pydantic_settings import BaseSettings, SettingsConfigDict

from app.core.constants import EMBEDDING_DIMENSIONS


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    aws_region: str = "us-east-1"
    aws_access_key_id: str = ""
    aws_secret_access_key: str = ""
    bedrock_embedding_model: str = "amazon.titan-embed-text-v2:0"
    bedrock_embedding_dimensions: int = EMBEDDING_DIMENSIONS
    bedrock_chat_model: str = "us.anthropic.claude-sonnet-4-6"
    bedrock_rerank_model: str = ""
    database_url: str = "postgresql+psycopg://search:search@localhost:5432/search"
    cors_origins: str = "http://localhost:5173"
    chunk_max_chars: int = 1200
    chunk_overlap_chars: int = 200
    retrieval_candidates: int = 20
    rerank_top_k: int = 6
    rrf_k: int = 60
    max_upload_bytes: int = 15 * 1024 * 1024
    max_query_chars: int = 4000
    chat_history_messages: int = 6

    @property
    def cors_origin_list(self) -> list[str]:
        return [item.strip() for item in self.cors_origins.split(",") if item.strip()]


@lru_cache
def get_settings() -> Settings:
    settings = Settings()
    if settings.bedrock_embedding_dimensions != EMBEDDING_DIMENSIONS:
        raise RuntimeError(
            "BEDROCK_EMBEDDING_DIMENSIONS must match the database vector column "
            f"({EMBEDDING_DIMENSIONS}). Change both together with a migration."
        )
    if settings.chunk_overlap_chars < 0 or settings.chunk_overlap_chars >= settings.chunk_max_chars:
        raise RuntimeError("CHUNK_OVERLAP_CHARS must be smaller than CHUNK_MAX_CHARS.")
    if settings.rerank_top_k < 1 or settings.retrieval_candidates < settings.rerank_top_k:
        raise RuntimeError("RETRIEVAL_CANDIDATES must be at least RERANK_TOP_K.")
    return settings
