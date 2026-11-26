from __future__ import annotations

from typing import Any

from app.utils.hashing import content_fingerprint


def assignment_fingerprint(item: dict[str, Any]) -> str:
    return content_fingerprint(
        str(item.get("title") or ""),
        str(item.get("description") or ""),
        str(item.get("instructions") or ""),
        str(item.get("deadline") or ""),
        str(item.get("total_marks") or ""),
        str(item.get("submission_type") or ""),
        str(item.get("assignment_type") or ""),
    )


def classify_workflow(portal_status: str | None, deadline: str | None, is_submitted: bool = False) -> str:
    normalized = (portal_status or "").strip().lower()
    if is_submitted or normalized in {"submitted", "evaluated", "graded"}:
        return "submitted"
    if normalized in {"closed", "expired"}:
        return "pending"
    return "new"


def diff_assignment(existing: dict[str, Any] | None, incoming: dict[str, Any]) -> tuple[str, list[dict[str, Any]]]:
    if existing is None:
        return "created", []
    events: list[dict[str, Any]] = []
    fields = ["title", "description", "instructions", "deadline", "total_marks", "submission_type", "assignment_type", "portal_status"]
    for field in fields:
        old, new = existing.get(field), incoming.get(field)
        if old != new:
            event_type = "deadline_changed" if field == "deadline" else f"{field}_changed"
            events.append({"event_type": event_type, "old_value": old, "new_value": new})
    return ("updated" if events else "unchanged"), events
