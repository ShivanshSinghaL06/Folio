from app.core.config import Settings
from app.services.answering import NO_MATCH_ANSWER, compose_answer
from app.services.reranking.feature import FeatureReranker
from app.services.retrieval.pipeline import run_retrieval
from app.services.retrieval.types import RetrievedChunk


class FakeEmbedder:
    def embed_query(self, text: str) -> list[float]:
        self.query = text
        return [0.1, 0.2]


class FakeLexical:
    def __init__(self, hits):
        self.hits = hits

    def search(self, db, query, *, limit, document_ids):
        return self.hits


class FakeVector:
    def __init__(self, hits):
        self.hits = hits
        self.embedding = None

    def search(self, db, embedding, *, limit, document_ids):
        self.embedding = embedding
        return self.hits


class FakeGenerator:
    def __init__(self):
        self.called = False

    def generate(self, *, query, chunks, history):
        self.called = True
        self.query = query
        self.chunks = chunks
        return f"{chunks[0].content} [1]"


class ReadyDb:
    def scalar(self, _statement):
        return 1


def _settings() -> Settings:
    return Settings(
        chunk_max_chars=1200,
        chunk_overlap_chars=200,
        retrieval_candidates=5,
        rerank_top_k=2,
        rrf_k=60,
    )


def test_retrieval_fuses_then_reranks():
    lexical_hit = RetrievedChunk(
        chunk_id="lexical",
        document_id="d",
        document_name="a.pdf",
        content="invoice number 4481",
        lexical_score=3.0,
        page_start=4,
    )
    vector_hit = RetrievedChunk(
        chunk_id="vector",
        document_id="d",
        document_name="a.pdf",
        content="unrelated cooking paragraph",
        vector_score=0.99,
    )
    vector = FakeVector([vector_hit])
    ranked = run_retrieval(
        None,
        "invoice number",
        embedder=FakeEmbedder(),
        lexical=FakeLexical([lexical_hit]),
        vector=vector,
        reranker=FeatureReranker(),
        settings=_settings(),
        document_ids=None,
    )
    assert ranked[0].chunk_id == "lexical"
    assert ranked[0].page_start == 4
    assert vector.embedding == [0.1, 0.2]


def test_compose_answer_does_not_call_the_model_when_nothing_matches():
    generator = FakeGenerator()
    result = compose_answer(
        ReadyDb(),
        "where is the contract?",
        [],
        document_ids=None,
        embedder=FakeEmbedder(),
        lexical=FakeLexical([]),
        vector=FakeVector([]),
        reranker=FeatureReranker(),
        generator=generator,
        settings=_settings(),
    )
    assert result.text == NO_MATCH_ANSWER
    assert result.citations == []
    assert generator.called is False


def test_compose_answer_cites_the_passage_the_model_used():
    hit = RetrievedChunk(
        chunk_id="11111111-1111-1111-1111-111111111111",
        document_id="22222222-2222-2222-2222-222222222222",
        document_name="policy.docx",
        content="Employees receive twenty days of leave.",
        section_title="Leave policy",
    )
    result = compose_answer(
        ReadyDb(),
        "How many leave days?",
        [("user", "Tell me about leave")],
        document_ids=None,
        embedder=FakeEmbedder(),
        lexical=FakeLexical([hit]),
        vector=FakeVector([]),
        reranker=FeatureReranker(),
        generator=FakeGenerator(),
        settings=_settings(),
    )
    assert "[1]" in result.text
    assert result.citations[0].document_name == "policy.docx"
    assert result.citations[0].section_title == "Leave policy"
    assert result.citations[0].cited_inline is True
