"""Rerank fused candidates with term coverage, phrase match, and retrieval scores."""

from dataclasses import replace

from app.services.retrieval.tokenize import tokenize
from app.services.retrieval.types import RetrievedChunk


class FeatureReranker:
    def rerank(self, query: str, candidates: list[RetrievedChunk], limit: int) -> list[RetrievedChunk]:
        if limit < 1:
            return []
        terms = set(tokenize(query))
        prepared = " ".join(query.lower().split())
        scored: list[tuple[float, str, RetrievedChunk]] = []
        for candidate in candidates:
            score = self._score(prepared, terms, candidate)
            scored.append((score, candidate.chunk_id, candidate))
        scored.sort(key=lambda item: (-item[0], item[1]))
        return [replace(candidate, rerank_score=score) for score, _chunk_id, candidate in scored[:limit]]

    def _score(self, query: str, terms: set[str], candidate: RetrievedChunk) -> float:
        tokens = set(tokenize(candidate.content))
        coverage = (len(terms & tokens) / len(terms)) if terms else 0.0
        phrase = 1.0 if query and query in candidate.content.lower() else 0.0
        section = (candidate.section_title or "").lower()
        title_hit = 1.0 if terms and any(term in section for term in terms) else 0.0
        vector = _unit(candidate.vector_score)
        lexical = _squash(candidate.lexical_score)
        return 0.35 * coverage + 0.20 * phrase + 0.10 * title_hit + 0.20 * vector + 0.15 * lexical


def _unit(value: float | None) -> float:
    if value is None:
        return 0.0
    return max(0.0, min(float(value), 1.0))


def _squash(value: float | None) -> float:
    if value is None or value <= 0:
        return 0.0
    number = float(value)
    return number / (1.0 + number)
