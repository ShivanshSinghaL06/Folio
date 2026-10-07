import math

from app.services.retrieval.bm25 import bm25_scores


def test_term_match_outranks_a_document_without_the_term():
    scores = dict(
        bm25_scores(
            "cat",
            [("one", "the cat sat on the mat"), ("two", "the dog sat on the log")],
            document_count=2,
            document_frequencies={"cat": 1},
            average_document_length=6,
        )
    )
    assert scores["one"] > scores["two"]
    assert scores["two"] == 0


def test_rare_term_scores_higher_than_a_term_in_every_document():
    documents = [("rare", "unique widget"), ("common", "shared shared")]
    rare = dict(
        bm25_scores(
            "widget",
            documents,
            document_count=2,
            document_frequencies={"widget": 1},
            average_document_length=2,
        )
    )
    common = dict(
        bm25_scores(
            "shared",
            documents,
            document_count=2,
            document_frequencies={"shared": 2},
            average_document_length=2,
        )
    )
    assert rare["rare"] > common["common"]


def test_empty_query_scores_zero():
    scores = bm25_scores(
        "!!!",
        [("one", "alpha")],
        document_count=1,
        document_frequencies={},
        average_document_length=1,
    )
    assert scores == [("one", 0.0)]
    assert math.isfinite(scores[0][1])
