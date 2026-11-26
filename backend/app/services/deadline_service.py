from datetime import datetime, timedelta, timezone

REMINDER_OFFSETS = {
    "7_days": timedelta(days=7),
    "3_days": timedelta(days=3),
    "1_day": timedelta(days=1),
    "6_hours": timedelta(hours=6),
    "1_hour": timedelta(hours=1),
}


def due_reminder_kinds(deadline: datetime, now: datetime | None = None) -> list[str]:
    now = now or datetime.now(timezone.utc)
    if deadline.tzinfo is None:
        deadline = deadline.replace(tzinfo=timezone.utc)
    result = []
    for name, offset in REMINDER_OFFSETS.items():
        target = deadline - offset
        if now >= target and now < target + timedelta(minutes=15):
            result.append(name)
    return result
