from app.services.generation.citations import build_citations, inline_citation_indexes
from app.services.generation.prompt import SYSTEM_PROMPT, build_user_prompt, format_location, trim_history
from app.services.retrieval.types import RetrievedChunk


def _chunk() -> RetrievedChunk:
    return RetrievedChunk(
        chunk_id="c1",
        document_id="d1",
        document_name="policy.docx",
        content="Employees receive twenty days of leave.",
        section_title="Leave policy",
        page_start=None,
    )


def test_location_label_for_pages_and_sections():
    assert format_location(4, 4, None) == "page 4"
    assert format_location(4, 6, "Terms") == "Terms · pages 4-6"
    assert format_location(None, None, "Leave policy") == "Leave policy"


def test_inline_markers_keep_first_seen_order():
    assert inline_citation_indexes("See [2] and [1] and [2].") == [2, 1]


def test_citations_record_the_source_and_whether_it_was_marked():
    citations = build_citations([_chunk()], "Leave is twenty days [1].")
    assert citations[0].document_name == "policy.docx"
    assert citations[0].section_title == "Leave policy"
    assert citations[0].cited_inline is True
    assert "twenty days" in citations[0].excerpt
    assert citations[0].as_dict()["index"] == 1


def test_prompt_includes_numbered_source_and_history():
    prompt = build_user_prompt(
        "How much leave?",
        [_chunk()],
        [("user", "What policies exist?"), ("assistant", "There is a leave policy [1].")],
    )
    assert "Conversation so far:" in prompt
    assert "[1] policy.docx (Leave policy)" in prompt
    assert "Question: How much leave?" in prompt
    assert "reference material" in SYSTEM_PROMPT


def test_history_is_trimmed():
    messages = [("user", "one"), ("assistant", "two"), ("user", "three")]
    assert trim_history(messages, limit=2) == [("assistant", "two"), ("user", "three")]
    assert trim_history(messages, limit=0) == []
    long = trim_history([("user", "a" * 50)], limit=1, max_chars=10)
    assert len(long[0][1]) == 10
