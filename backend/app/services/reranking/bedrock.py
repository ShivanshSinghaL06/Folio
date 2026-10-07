"""Optional Bedrock rerank. Falls back to the local feature reranker."""

from __future__ import annotations

import json
import logging
from dataclasses import replace

from app.services.reranking.feature import FeatureReranker
from app.services.retrieval.types import RetrievedChunk

logger = logging.getLogger(__name__)


def cohere_rerank_request(query: str, documents: list[str], top_n: int) -> dict:
    return {
        "api_version": 2,
        "query": query,
        "documents": documents,
        "top_n": top_n,
    }


class BedrockReranker:
    def __init__(self, client, model_id: str, fallback: FeatureReranker) -> None:
        self._client = client
        self._model_id = model_id
        self._fallback = fallback

    def rerank(self, query: str, candidates: list[RetrievedChunk], limit: int) -> list[RetrievedChunk]:
        if not candidates or limit < 1:
            return []
        try:
            body = cohere_rerank_request(query, [item.content for item in candidates], limit)
            response = self._client.invoke_model(
                modelId=self._model_id,
                body=json.dumps(body),
                accept="application/json",
                contentType="application/json",
            )
            payload = json.loads(response["body"].read())
            ordered: list[RetrievedChunk] = []
            for item in payload.get("results") or []:
                index = int(item["index"])
                if not 0 <= index < len(candidates):
                    continue
                score = float(item.get("relevance_score", 0.0))
                ordered.append(replace(candidates[index], rerank_score=score))
            if not ordered:
                return self._fallback.rerank(query, candidates, limit)
            return ordered[:limit]
        except Exception as exc:
            logger.warning("Bedrock rerank failed (%s); using the local reranker.", type(exc).__name__)
            return self._fallback.rerank(query, candidates, limit)


def build_reranker(client, model_id: str) -> FeatureReranker | BedrockReranker:
    feature = FeatureReranker()
    if model_id.strip():
        return BedrockReranker(client, model_id.strip(), feature)
    return feature
