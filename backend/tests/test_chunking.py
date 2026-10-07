from app.services.ingestion.chunk import chunk_blocks
from app.services.ingestion.types import TextBlock


def test_short_blocks_stay_together_and_keep_page_span():
    drafts = chunk_blocks(
        [
            TextBlock("Page one text", page=1, section="Intro"),
            TextBlock("Page three text", page=3, section="Details"),
        ],
        max_chars=200,
        overlap=20,
    )
    assert len(drafts) == 1
    assert drafts[0].page_start == 1
    assert drafts[0].page_end == 3
    assert drafts[0].section_title == "Intro"
    assert drafts[0].chunk_index == 0


def test_overlap_carries_the_tail_into_the_next_chunk():
    first = "a" * 100
    second = "b" * 100
    third = "c" * 100
    drafts = chunk_blocks(
        [
            TextBlock(first, page=1),
            TextBlock(second, page=1),
            TextBlock(third, page=2),
        ],
        max_chars=250,
        overlap=100,
    )
    assert [draft.content for draft in drafts] == [f"{first}\n{second}", f"{second}\n{third}"]
    assert drafts[1].page_start == 1
    assert drafts[1].page_end == 2


def test_long_text_splits_on_spaces():
    text = " ".join(["word"] * 80)
    drafts = chunk_blocks([TextBlock(text)], max_chars=200, overlap=20)
    assert len(drafts) > 1
    assert all(len(draft.content) <= 200 for draft in drafts)
    assert drafts[0].content.startswith("word")


def test_blank_blocks_are_dropped():
    assert chunk_blocks([TextBlock("   "), TextBlock("")], max_chars=200, overlap=20) == []
