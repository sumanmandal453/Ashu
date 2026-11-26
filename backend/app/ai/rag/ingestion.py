from app.ai.rag.chunking import chunk_text
from app.ai.rag.embeddings import embed_texts
from app.documents.extract import extract_text


async def ingest_document(filename: str, data: bytes) -> list[dict]:
    text = extract_text(filename, data)
    chunks = chunk_text(text)
    embeddings = await embed_texts(chunks) if chunks else []
    return [{"chunk_text": chunk, "embedding": vector, "chunk_index": i} for i, (chunk, vector) in enumerate(zip(chunks, embeddings))]
