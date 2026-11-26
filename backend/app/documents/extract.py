from __future__ import annotations

from io import BytesIO
from pathlib import Path


def extract_text(filename: str, data: bytes) -> str:
    ext = Path(filename).suffix.lower()
    if ext == ".pdf":
        import fitz
        doc = fitz.open(stream=data, filetype="pdf")
        return "\n".join(page.get_text("text") for page in doc)
    if ext == ".docx":
        from docx import Document
        doc = Document(BytesIO(data))
        return "\n".join(p.text for p in doc.paragraphs if p.text.strip())
    if ext == ".pptx":
        from pptx import Presentation
        prs = Presentation(BytesIO(data))
        parts = []
        for slide in prs.slides:
            for shape in slide.shapes:
                if hasattr(shape, "text") and shape.text.strip():
                    parts.append(shape.text)
        return "\n".join(parts)
    if ext == ".txt":
        return data.decode("utf-8", errors="replace")
    raise ValueError(f"Unsupported document format: {ext}")
