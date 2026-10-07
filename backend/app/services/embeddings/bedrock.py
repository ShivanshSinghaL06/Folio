"""Amazon Titan embedding requests."""

from __future__ import annotations

import json

from app.core.bedrock import raise_bedrock
from app.core.config import Settings
from app.core.constants import EMBEDDING_DIMENSIONS
from app.core.errors import AppError


def titan_embed_request(text: str, dimensions: int) -> dict:
    return {
        "inputText": text,
        "dimensions": dimensions,
        "normalize": True,
    }


class BedrockEmbedder:
    def __init__(self, client, settings: Settings) -> None:
        self._client = client
        self._model_id = settings.bedrock_embedding_model
        self._dimensions = settings.bedrock_embedding_dimensions

    def embed_query(self, text: str) -> list[float]:
        return self._embed_one(text)

    def embed_texts(self, texts: list[str]) -> list[list[float]]:
        return [self._embed_one(text) for text in texts]

    def _embed_one(self, text: str) -> list[float]:
        body = titan_embed_request(text[:20000], self._dimensions)
        try:
            response = self._client.invoke_model(
                modelId=self._model_id,
                body=json.dumps(body),
                accept="application/json",
                contentType="application/json",
            )
            payload = json.loads(response["body"].read())
        except AppError:
            raise
        except Exception as exc:
            raise_bedrock(exc)
        embedding = payload.get("embedding")
        if not isinstance(embedding, list) or len(embedding) != EMBEDDING_DIMENSIONS:
            raise AppError(
                "The embedding model returned a vector that does not match the database dimension.",
                502,
            )
        return [float(value) for value in embedding]
