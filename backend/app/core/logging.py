import logging
import re

from app.core.config import settings

_SECRET_PATTERNS = [
    re.compile(r"(Bearer\s+)[A-Za-z0-9._~-]+", re.IGNORECASE),
    re.compile(r"(Auth-Token[\":= ]+)[^\", ]+", re.IGNORECASE),
    re.compile(r"(api[_-]?key[\":= ]+)[^\", ]+", re.IGNORECASE),
]


class RedactingFilter(logging.Filter):
    def filter(self, record: logging.LogRecord) -> bool:
        message = record.getMessage()
        for pattern in _SECRET_PATTERNS:
            message = pattern.sub(r"\1[REDACTED]", message)
        record.msg = message
        record.args = ()
        return True


def configure_logging() -> None:
    logging.basicConfig(
        level=getattr(logging, settings.log_level.upper(), logging.INFO),
        format="%(asctime)s %(levelname)s %(name)s %(message)s",
    )
    for handler in logging.getLogger().handlers:
        handler.addFilter(RedactingFilter())
