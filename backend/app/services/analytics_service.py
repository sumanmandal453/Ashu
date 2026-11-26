from collections import Counter
from datetime import datetime, timezone


def assignment_analytics(rows: list[dict]) -> dict:
    now = datetime.now(timezone.utc)
    counts = Counter()
    subject_counts = Counter()
    completed = 0
    overdue = 0
    for row in rows:
        status = row.get("workflow_status") or "new"
        counts[status] += 1
        subject_counts[row.get("subject_name") or "Uncategorized"] += 1
        if row.get("portal_is_submitted"):
            completed += 1
        deadline = row.get("deadline")
        if deadline and not row.get("portal_is_submitted"):
            try:
                dt = datetime.fromisoformat(deadline.replace("Z", "+00:00"))
                if dt < now:
                    overdue += 1
            except ValueError:
                pass
    return {"total": len(rows), "new": counts["new"], "pending": counts["pending"],
            "in_progress": counts["in_progress"], "ai_generated": counts["ai_generated"],
            "awaiting_approval": counts["awaiting_approval"], "submitted": completed,
            "overdue": overdue, "by_subject": dict(subject_counts)}


def weekly_completion(rows: list[dict], weeks: int = 6) -> list[dict]:
    from datetime import timedelta
    now = datetime.now(timezone.utc)
    monday = (now - timedelta(days=now.weekday())).replace(hour=0, minute=0, second=0, microsecond=0)
    buckets = []
    for offset in reversed(range(weeks)):
        start = monday - timedelta(weeks=offset)
        end = start + timedelta(weeks=1)
        count = 0
        for row in rows:
            stamp = row.get("verified_at") or row.get("created_at")
            if not stamp:
                continue
            try:
                dt = datetime.fromisoformat(stamp.replace("Z", "+00:00"))
                if start <= dt < end and row.get("submission_status") == "submitted":
                    count += 1
            except ValueError:
                continue
        buckets.append({"week_start": start.date().isoformat(), "label": f"W{len(buckets)+1}", "count": count})
    return buckets
