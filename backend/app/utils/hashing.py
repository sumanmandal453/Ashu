import hashlib


def sha256_bytes(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def content_fingerprint(*parts: str | None) -> str:
    normalized = "\x1f".join((p or "").strip() for p in parts)
    return hashlib.sha256(normalized.encode("utf-8")).hexdigest()
