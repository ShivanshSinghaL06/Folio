from app.services.retrieval.fusion import reciprocal_rank_fusion
from app.services.retrieval.pipeline import fuse_hits
from app.services.retrieval.types import RetrievedChunk


def test_shared_hit_outranks_a_single_list_hit():
    ranking = reciprocal_rank_fusion([["a", "b"], ["b", "c"]], k=60)
    scores = dict(ranking)
    assert scores["b"] > scores["a"]
    assert scores["b"] > scores["c"]
    assert [item_id for item_id, _score in ranking][0] == "b"


def test_duplicate_ids_in_one_list_are_counted_once():
    once = dict(reciprocal_rank_fusion([["a"]], k=60))
    twice = dict(reciprocal_rank_fusion([["a", "a"]], k=60))
    assert once == twice


def test_fuse_hits_keeps_both_scores():
    lexical = [
        RetrievedChunk(
            chunk_id="a",
            document_id="d",
            document_name="policy.pdf",
            content="alpha",
            lexical_score=1.5,
            page_start=2,
        )
    ]
    vector = [
        RetrievedChunk(
            chunk_id="a",
            document_id="d",
            document_name="policy.pdf",
            content="alpha",
            vector_score=0.8,
            page_start=2,
        )
    ]
    fused = fuse_hits(lexical, vector, k=60, limit=5)
    assert len(fused) == 1
    assert fused[0].lexical_score == 1.5
    assert fused[0].vector_score == 0.8
    assert fused[0].fusion_score is not None
    assert fused[0].page_start == 2
