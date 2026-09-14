from ingest.chunk import ParentChildChunker


def test_parent_child_chunker_basic():
    text = "# A\n" + ("para " * 200) + "\n# B\n" + ("para " * 200)
    chunks = ParentChildChunker().split(text)
    assert any(c.parent_text for c in chunks)
    assert all(c.child_text.strip() for c in chunks)
