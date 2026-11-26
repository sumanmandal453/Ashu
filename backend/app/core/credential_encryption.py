from cryptography.fernet import Fernet, InvalidToken
from app.core.config import settings


def _fernet() -> Fernet:
    if not settings.integration_encryption_key:
        raise RuntimeError("INTEGRATION_ENCRYPTION_KEY is not configured")
    return Fernet(settings.integration_encryption_key.encode())


def encrypt_credential(value: str) -> str:
    return _fernet().encrypt(value.encode()).decode()


def decrypt_credential(value: str) -> str:
    try:
        return _fernet().decrypt(value.encode()).decode()
    except InvalidToken as exc:
        raise RuntimeError("Stored integration credential could not be decrypted") from exc
