from app.ai.rag.chunking import chunk_text


def test_chunk_text_empty():
    assert chunk_text("   ") == []


def test_chunk_text_respects_size_and_overlap():
    text = "a" * 2500
    chunks = chunk_text(text, chunk_size=1000, overlap=100)
    assert len(chunks) == 3
    assert all(len(chunk) <= 1000 for chunk in chunks)
    assert chunks[0][-100:] == chunks[1][:100]


def test_chunk_text_preserves_all_content_when_joined_with_overlap():
    text = "word " * 600
    chunks = chunk_text(text, chunk_size=500, overlap=50)
    assert chunks
    assert chunks[0].startswith("word")
