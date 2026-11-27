
from __future__ import annotations

from datetime import datetime, timedelta, timezone
from typing import Any


# Bhawanipur Digiicampus uses Indian Standard Time.
# Naive portal timestamps are interpreted as IST and converted to UTC.
PORTAL_TIMEZONE = timezone(timedelta(hours=5, minutes=30))


def _unwrap(payload: Any) -> list[dict[str, Any]]:
    """
    Extract records from Digiicampus response envelopes.

    Supports:
    - Direct lists
    - Bhawanipur's 'res' response wrapper
    - previousAssignments
    - upcomingAssignments
    - draftAssignments
    - Common API response wrappers
    - Individual assignment-detail responses
    """

    if isinstance(payload, list):
        return [item for item in payload if isinstance(item, dict)]

    if not isinstance(payload, dict):
        return []

    # Unwrap common response containers, including Bhawanipur's "res".
    for key in ("res", "data", "result", "results", "content"):
        value = payload.get(key)

        if isinstance(value, list):
            return [item for item in value if isinstance(item, dict)]

        if isinstance(value, dict):
            nested = _unwrap(value)

            if nested:
                return nested

    # Handle Bhawanipur's assignment categories.
    categorized: list[dict[str, Any]] = []

    for key in (
        "previousAssignments",
        "upcomingAssignments",
        "draftAssignments",
    ):
        value = payload.get(key)

        if isinstance(value, list):
            categorized.extend(
                item for item in value if isinstance(item, dict)
            )

    if categorized:
        return categorized

    # Recognize a single assignment-detail response.
    if (
        "id" in payload
        and "name" in payload
        and any(
            key in payload
            for key in (
                "dueDate",
                "startDate",
                "submissionType",
                "assignmentType",
            )
        )
    ):
        return [payload]

    # Recognize a single course or assignment record.
    if any(
        key in payload
        for key in (
            "assignmentId",
            "assignment_id",
            "assignmentName",
            "courseName",
            "className",
            "course_name",
        )
    ):
        return [payload]

    # Handle other common collections.
    for key in (
        "courses",
        "assignments",
        "resources",
        "modules",
        "sessions",
        "events",
        "posts",
    ):
        value = payload.get(key)

        if isinstance(value, list):
            return [item for item in value if isinstance(item, dict)]

    return []


def _first(item: dict[str, Any], *keys: str) -> Any:
    """Return the first available, non-empty field."""

    for key in keys:
        value = item.get(key)

        if value is not None and value != "":
            return value

    return None


def normalize_courses(payload: Any) -> list[dict[str, Any]]:
    """
    Convert Bhawanipur Digiicampus course records into Ashu's format.

    Bhawanipur classroom response example:
    {
        "courseId": 1076,
        "courseName": "Data Mining [MDS302]",
        "courseCode": "MDS302",
        "id": 10041,
        "courseComponentTypeName": "Theory"
    }
    """

    result: list[dict[str, Any]] = []

    for item in _unwrap(payload):
        name = _first(
            item,
            "courseName",
            "className",
            "name",
            "course_name",
            "title",
        )

        if not name:
            continue

        result.append(
            {
                # Course identifier, e.g. 1076.
                "external_course_id": (
                    str(_first(item, "courseId", "course_id", "id") or "")
                    or None
                ),

                # Class identifier, e.g. 10041.
                # This is the ID required by the assignment-list endpoint.
                "external_class_id": (
                    str(_first(item, "classId", "class_id", "id") or "")
                    or None
                ),

                "course_name": str(name),

                "course_code": (
                    str(
                        _first(
                            item,
                            "courseCode",
                            "code",
                            "course_code",
                        )
                        or ""
                    )
                    or None
                ),

                "faculty_name": _first(
                    item,
                    "facultyName",
                    "faculty",
                    "faculty_name",
                ),

                # IMPORTANT:
                # Bhawanipur uses courseComponentTypeName,
                # such as Theory, Practical and Lecture.
                "course_type": _first(
                    item,
                    "courseComponentTypeName",
                    "type",
                    "courseType",
                    "course_type",
                ),

                "course_status": _first(
                    item,
                    "status",
                    "courseStatus",
                ),

                # Preserve the original portal record.
                "raw_source": item,
            }
        )

    return result


def _parse_datetime(value: Any) -> str | None:
    """
    Convert Digiicampus dates into UTC ISO-8601 strings.

    Handles:
    - Unix timestamps in seconds
    - Unix timestamps in milliseconds
    - ISO-8601 timestamps
    - Bhawanipur timestamps such as:
      2026-09-10 17:24:00
    - Common display-date formats
    """

    if value is None or value == "":
        return None

    # Handle Unix timestamps.
    if isinstance(value, (int, float)) and not isinstance(value, bool):
        try:
            timestamp = (
                value / 1000
                if abs(value) > 10_000_000_000
                else value
            )

            dt = datetime.fromtimestamp(
                timestamp,
                tz=timezone.utc,
            )

            return dt.isoformat()

        except (ValueError, OSError, OverflowError):
            return None

    if not isinstance(value, str):
        return None

    candidate = value.strip()

    # Handle ISO-8601 timestamps, including those ending in Z.
    iso_candidate = (
        candidate[:-1] + "+00:00"
        if candidate.endswith("Z")
        else candidate
    )

    try:
        dt = datetime.fromisoformat(iso_candidate)

        # Portal timestamps without timezone information are IST.
        if dt.tzinfo is None:
            dt = dt.replace(tzinfo=PORTAL_TIMEZONE)

        return dt.astimezone(timezone.utc).isoformat()

    except ValueError:
        pass

    # Handle alternative date formats.
    formats = (
        "%b %d, %Y, %I:%M %p",
        "%b %d, %Y %I:%M %p",
        "%b %d, %Y",
        "%d %b %Y",
        "%Y-%m-%d",
    )

    for fmt in formats:
        try:
            dt = datetime.strptime(candidate, fmt)
            dt = dt.replace(tzinfo=PORTAL_TIMEZONE)

            return dt.astimezone(timezone.utc).isoformat()

        except ValueError:
            continue

    return None


def normalize_assignments(
    payload: Any,
    class_id: str | None = None,
) -> list[dict[str, Any]]:
    """
    Convert Bhawanipur Digiicampus assignments into Ashu's format.

    Supports assignment-list and individual assignment-detail responses.
    """

    result: list[dict[str, Any]] = []

    for item in _unwrap(payload):
        external_id = _first(
            item,
            "assignmentId",
            "id",
            "assignment_id",
        )

        title = _first(
            item,
            "assignmentName",
            "title",
            "name",
            "assignmentTitle",
        )

        # Assignment ID and title are required.
        if external_id is None or not title:
            continue

        external_class_id = (
            _first(item, "classId", "class_id") or class_id
        )

        result.append(
            {
                "external_assignment_id": str(external_id),

                "external_class_id": (
                    str(external_class_id)
                    if external_class_id is not None
                    else None
                ),

                "title": str(title),

                "description": _first(
                    item,
                    "description",
                    "assignmentDescription",
                ),

                "instructions": _first(
                    item,
                    "instructions",
                    "instruction",
                ),

                "start_at": _parse_datetime(
                    _first(
                        item,
                        "startDate",
                        "startAt",
                        "start_date",
                    )
                ),

                "deadline": _parse_datetime(
                    _first(
                        item,
                        "dueDate",
                        "dueAt",
                        "due_date",
                        "deadline",
                    )
                ),

                "submission_type": _first(
                    item,
                    "submissionType",
                    "submission_type",
                ),

                "assignment_type": _first(
                    item,
                    "assignmentType",
                    "type",
                ),

                "grading_type": _first(
                    item,
                    "grading",
                    "gradingType",
                    "grading_type",
                    "rubricGrading",
                ),

                "total_marks": _first(
                    item,
                    "totalMarks",
                    "maxMarks",
                    "marks",
                    "assignmentMarks",
                    "maximumMarks",
                ),

                "portal_status": _first(
                    item,
                    "status",
                    "assignmentStatus",
                    "submissionStatus",
                ),

                # Preserve the original portal response.
                "raw_source": item,
            }
        )

    return result
