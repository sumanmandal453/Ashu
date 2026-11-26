def chunk_text(text: str, chunk_size: int = 1200, overlap: int = 150) -> list[str]:
    cleaned = " ".join(text.split())
    if not cleaned:
        return []
    chunks = []
    start = 0
    while start < len(cleaned):
        end = min(len(cleaned), start + chunk_size)
        chunks.append(cleaned[start:end])
        if end == len(cleaned):
            break
        start = max(end - overlap, start + 1)
    return chunks
