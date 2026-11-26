import pytest
from app.utils.file_validation import validate_upload


def test_valid_pdf_upload():
    validate_upload("assignment.pdf", "application/pdf", 1024, 2048)


def test_reject_mismatched_content_type():
    with pytest.raises(ValueError):
        validate_upload("assignment.pdf", "text/plain", 1024, 2048)


def test_reject_oversized_file():
    with pytest.raises(ValueError):
        validate_upload("assignment.pdf", "application/pdf", 4096, 2048)


def test_reject_unsupported_extension():
    with pytest.raises(ValueError):
        validate_upload("payload.exe", "application/octet-stream", 1024, 2048)
