from pathlib import Path

ALLOWED_UPLOADS = {
    ".pdf": {"application/pdf"},
    ".docx": {"application/vnd.openxmlformats-officedocument.wordprocessingml.document"},
    ".pptx": {"application/vnd.openxmlformats-officedocument.presentationml.presentation"},
    ".txt": {"text/plain"},
    ".png": {"image/png"},
    ".jpg": {"image/jpeg"},
    ".jpeg": {"image/jpeg"},
}


def validate_upload(filename: str, content_type: str, size: int, max_bytes: int) -> None:
    ext = Path(filename).suffix.lower()
    if ext not in ALLOWED_UPLOADS:
        raise ValueError("Unsupported file extension")
    if content_type not in ALLOWED_UPLOADS[ext]:
        raise ValueError("File content type does not match the file extension")
    if size <= 0 or size > max_bytes:
        raise ValueError(f"File must be between 1 byte and {max_bytes} bytes")
