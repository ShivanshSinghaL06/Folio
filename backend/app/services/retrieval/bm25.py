"""Okapi BM25 over a candidate set."""

from __future__ import annotations

import math
from collections import Counter

from app.services.retrieval.tokenize import tokenize

K1 = 1.5
B = 0.75


def bm25_scores(
    query: str,
    documents: list[tuple[str, str]],
    *,
    document_count: int,
    document_frequencies: dict[str, int],
    average_document_length: float,
    k1: float = K1,
    b: float = B,
) -> list[tuple[str, float]]:
    terms = list(dict.fromkeys(tokenize(query)))
    if not terms or document_count <= 0 or average_document_length <= 0:
        return [(doc_id, 0.0) for doc_id, _text in documents]

    scored: list[tuple[str, float]] = []
    for doc_id, text in documents:
        tokens = tokenize(text)
        length = len(tokens) or 1
        frequencies = Counter(tokens)
        score = 0.0
        for term in terms:
            frequency = frequencies.get(term, 0)
            if frequency == 0:
                continue
            df = document_frequencies.get(term, 0)
            idf = math.log(1.0 + (document_count - df + 0.5) / (df + 0.5))
            denominator = frequency + k1 * (1.0 - b + b * length / average_document_length)
            score += idf * (frequency * (k1 + 1.0)) / denominator
        scored.append((doc_id, score))
    scored.sort(key=lambda item: (-item[1], item[0]))
    return scored
