from datetime import datetime, timezone
from zoneinfo import ZoneInfo


def utc_now() -> datetime:
    return datetime.now(timezone.utc)


def to_local(value: datetime, timezone_name: str = "Asia/Kolkata") -> datetime:
    if value.tzinfo is None:
        value = value.replace(tzinfo=timezone.utc)
    try:
        return value.astimezone(ZoneInfo(timezone_name))
    except Exception:
        return value.astimezone(ZoneInfo("Asia/Kolkata"))
