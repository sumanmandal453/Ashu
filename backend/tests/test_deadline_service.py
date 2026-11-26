from datetime import datetime, timezone, timedelta

from app.services.deadline_service import due_reminder_kinds


def test_due_reminder_kinds_inside_window():
    now = datetime(2026, 11, 24, 12, 0, tzinfo=timezone.utc)
    deadline = now + timedelta(days=1)
    assert due_reminder_kinds(deadline, now) == ["1_day"]


def test_due_reminder_kinds_outside_window():
    now = datetime(2026, 11, 24, 12, 0, tzinfo=timezone.utc)
    deadline = now + timedelta(days=2)
    assert due_reminder_kinds(deadline, now) == []


def test_naive_deadline_is_treated_as_utc():
    now = datetime(2026, 11, 24, 12, 0, tzinfo=timezone.utc)
    deadline = datetime(2026, 11, 24, 13, 0)
    assert due_reminder_kinds(deadline, now) == ["1_hour"]
