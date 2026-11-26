from __future__ import annotations

from datetime import datetime, timezone
from datetime import date
from typing import Any


def _unwrap(payload: Any) -> list[dict[str, Any]]:
    if isinstance(payload, list):
        return [x for x in payload if isinstance(x, dict)]
    if isinstance(payload, dict):
        if any(k in payload for k in ("assignmentId", "assignment_id", "assignmentName", "courseName", "className", "course_name")):
            return [payload]
        for key in ("data", "result", "results", "courses", "assignments", "content"):
            value = payload.get(key)
            if isinstance(value, list):
                return [x for x in value if isinstance(x, dict)]
            if isinstance(value, dict):
                nested = _unwrap(value)
                if nested:
                    return nested
    return []


def _first(item: dict[str, Any], *keys: str) -> Any:
    for key in keys:
        value = item.get(key)
        if value is not None and value != "":
            return value
    return None


def normalize_courses(payload: Any) -> list[dict[str, Any]]:
    result = []
    for item in _unwrap(payload):
        name = _first(item, "courseName", "className", "name", "course_name", "title")
        if not name:
            continue
        result.append({
            "external_course_id": str(_first(item, "courseId", "id", "course_id") or "") or None,
            "external_class_id": str(_first(item, "classId", "class_id", "id") or "") or None,
            "course_name": str(name),
            "course_code": str(_first(item, "courseCode", "code", "course_code") or "") or None,
            "faculty_name": _first(item, "facultyName", "faculty", "faculty_name"),
            "course_type": _first(item, "type", "courseType", "course_type"),
            "course_status": _first(item, "status", "courseStatus"),
            "raw_source": item,
        })
    return result


def _parse_datetime(value: Any) -> str | None:
    if value is None or value == "":
        return None
    if isinstance(value, (int, float)):
        try:
            dt = datetime.fromtimestamp(value / 1000 if value > 10_000_000_000 else value, tz=timezone.utc)
            return dt.isoformat()
        except (ValueError, OSError):
            return None
    if isinstance(value, str):
        candidate = value.strip().replace("Z", "+00:00")
        try:
            dt = datetime.fromisoformat(candidate)
            if dt.tzinfo is None:
                dt = dt.replace(tzinfo=timezone.utc)
            return dt.astimezone(timezone.utc).isoformat()
        except ValueError:
            for fmt in ("%b %d, %Y, %I:%M %p", "%b %d, %Y %I:%M %p", "%b %d, %Y", "%d %b %Y", "%Y-%m-%d"):
                try:
                    dt = datetime.strptime(candidate, fmt).replace(tzinfo=timezone.utc)
                    return dt.isoformat()
                except ValueError:
                    continue
            return None
    return None


def normalize_assignments(payload: Any, class_id: str | None = None) -> list[dict[str, Any]]:
    result = []
    for item in _unwrap(payload):
        external_id = _first(item, "assignmentId", "id", "assignment_id")
        title = _first(item, "assignmentName", "title", "name", "assignmentTitle")
        if external_id is None or not title:
            continue
        result.append({
            "external_assignment_id": str(external_id),
            "external_class_id": str(_first(item, "classId", "class_id") or class_id or "") or None,
            "title": str(title),
            "description": _first(item, "description", "assignmentDescription"),
            "instructions": _first(item, "instructions", "instruction"),
            "start_at": _parse_datetime(_first(item, "startDate", "startAt", "start_date")),
            "deadline": _parse_datetime(_first(item, "dueDate", "dueAt", "due_date", "deadline")),
            "submission_type": _first(item, "submissionType", "submission_type"),
            "assignment_type": _first(item, "assignmentType", "type"),
            "grading_type": _first(item, "grading", "gradingType"),
            "total_marks": _first(item, "totalMarks", "maxMarks", "marks"),
            "portal_status": _first(item, "status", "assignmentStatus"),
            "raw_source": item,
        })
    return result
