from __future__ import annotations

from app.documents.generate import generate_docx, generate_pdf
from app.utils.hashing import sha256_bytes


class DocumentService:
    def generate(self, *, file_format: str, title: str, student: dict, subject: str, qa: list[dict]):
        if file_format == "docx":
            data = generate_docx(title, student, subject, qa)
            content_type = "application/vnd.openxmlformats-officedocument.wordprocessingml.document"
            extension = "docx"
        elif file_format == "pdf":
            data = generate_pdf(title, student, subject, qa)
            content_type = "application/pdf"
            extension = "pdf"
        else:
            raise ValueError("Only PDF and DOCX are supported")
        return data, content_type, extension, sha256_bytes(data)
