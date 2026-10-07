import json

from app.services.reranking.bedrock import BedrockReranker, cohere_rerank_request
from app.services.reranking.feature import FeatureReranker
from app.services.retrieval.types import RetrievedChunk


def _chunk(chunk_id: str, content: str, **scores) -> RetrievedChunk:
    return RetrievedChunk(
        chunk_id=chunk_id,
        document_id="doc",
        document_name="notes.pdf",
        content=content,
        **scores,
    )


def test_feature_reranker_prefers_the_passage_that_contains_the_query():
    reranker = FeatureReranker()
    exact = _chunk(
        "exact",
        "The invoice number is 4481.",
        lexical_score=1.2,
        vector_score=0.4,
        section_title="Billing",
    )
    distractor = _chunk(
        "other",
        "A general introduction to cooking methods.",
        lexical_score=0.0,
        vector_score=0.95,
    )
    ranked = reranker.rerank("invoice number", [distractor, exact], limit=2)
    assert [item.chunk_id for item in ranked] == ["exact", "other"]
    assert ranked[0].rerank_score > ranked[1].rerank_score


def test_bedrock_reranker_reorders_using_model_indexes():
    class Body:
        def read(self):
            return json.dumps({"results": [{"index": 1, "relevance_score": 0.91}]}).encode()

    class Client:
        def invoke_model(self, **kwargs):
            self.kwargs = kwargs
            return {"body": Body()}

    client = Client()
    reranker = BedrockReranker(client, "cohere.rerank-v3-5:0", FeatureReranker())
    first = _chunk("first", "alpha")
    second = _chunk("second", "beta")
    ranked = reranker.rerank("beta", [first, second], limit=1)
    assert [item.chunk_id for item in ranked] == ["second"]
    assert ranked[0].rerank_score == 0.91
    sent = json.loads(client.kwargs["body"])
    assert sent == cohere_rerank_request("beta", ["alpha", "beta"], 1)


def test_bedrock_reranker_falls_back_when_the_model_call_fails():
    class Client:
        def invoke_model(self, **kwargs):
            raise RuntimeError("unavailable")

    reranker = BedrockReranker(Client(), "cohere.rerank-v3-5:0", FeatureReranker())
    exact = _chunk("exact", "invoice number 4481", lexical_score=2.0, vector_score=0.2)
    other = _chunk("other", "unrelated cooking notes", vector_score=0.99)
    ranked = reranker.rerank("invoice number", [other, exact], limit=1)
    assert ranked[0].chunk_id == "exact"
