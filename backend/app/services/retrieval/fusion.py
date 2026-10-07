"""Reciprocal rank fusion for two or more ranked lists."""


def reciprocal_rank_fusion(rankings: list[list[str]], *, k: int = 60) -> list[tuple[str, float]]:
    if k < 0:
        raise ValueError("k must be non-negative")
    scores: dict[str, float] = {}
    for ranking in rankings:
        seen: set[str] = set()
        for index, item_id in enumerate(ranking, start=1):
            if item_id in seen:
                continue
            seen.add(item_id)
            scores[item_id] = scores.get(item_id, 0.0) + 1.0 / (k + index)
    return sorted(scores.items(), key=lambda item: (-item[1], item[0]))
