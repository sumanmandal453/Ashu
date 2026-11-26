from __future__ import annotations

from datetime import datetime, timezone
from typing import Any

from app.database.repositories import Repository
from app.services.assignment_detector import assignment_fingerprint, classify_workflow, diff_assignment


class AssignmentService:
    def __init__(self, repo: Repository):
        self.repo = repo

    async def list_assignments(self, status_filter: str | None = None, subject_id: str | None = None, search: str | None = None, sort_by: str = "deadline", sort_order: str = "asc", page: int = 1, page_size: int = 20) -> tuple[list[dict[str, Any]], int]:
        rows = await self.repo.list_owned("assignments", limit=1000)
        now = datetime.now(timezone.utc)
        filtered = []
        for row in rows:
            deadline = row.get("deadline")
            try:
                deadline_dt = datetime.fromisoformat(deadline.replace("Z", "+00:00")) if deadline else None
            except (TypeError, ValueError):
                deadline_dt = None
            overdue = bool(deadline_dt and deadline_dt < now and not row.get("portal_is_submitted"))
            row["is_overdue"] = overdue
            derived = row.get("workflow_status") or "new"
            if overdue and derived not in {"submitted", "awaiting_approval"}:
                derived = "overdue"
            row["display_status"] = derived
            if status_filter and status_filter != "all":
                if status_filter == "overdue" and not overdue:
                    continue
                if status_filter != "overdue" and derived != status_filter:
                    continue
            if subject_id and row.get("subject_id") != subject_id:
                continue
            if search:
                needle = search.casefold()
                if needle not in (str(row.get("title", "")) + " " + str(row.get("subject_name", ""))).casefold():
                    continue
            filtered.append(row)
        reverse = sort_order.lower() == "desc"
        if sort_by not in {"deadline", "priority", "created_at", "title"}:
            sort_by = "deadline"
        filtered.sort(key=lambda r: (r.get(sort_by) is None, str(r.get(sort_by) or "")), reverse=reverse)
        total = len(filtered)
        start = (page - 1) * page_size
        return filtered[start:start + page_size], total

    async def upsert_portal_assignment(self, integration_id: str, course_id: str | None, user_id: str, item: dict[str, Any]) -> str:
        external_id = item["external_assignment_id"]
        class_id = item.get("external_class_id") or ""
        existing_rows = await self.repo.db.select(
            "assignments",
            query={"user_id": f"eq.{user_id}", "integration_id": f"eq.{integration_id}", "external_assignment_id": f"eq.{external_id}", "external_class_id": f"eq.{class_id}"},
            limit=1,
        )
        existing = existing_rows[0] if existing_rows else None
        fingerprint = assignment_fingerprint(item)
        values = {k: v for k, v in item.items() if k in {
            "external_assignment_id", "external_class_id", "title", "description", "instructions", "start_at", "deadline", "submission_type", "assignment_type", "grading_type", "total_marks", "portal_status", "subject_name"
        }}
        values.update({
            "user_id": user_id,
            "integration_id": integration_id,
            "course_id": course_id,
            "content_hash": fingerprint,
            "last_synced_at": datetime.now(timezone.utc).isoformat(),
        })
        event_type, events = diff_assignment(existing, values)
        if existing is None:
            values["workflow_status"] = classify_workflow(item.get("portal_status"), item.get("deadline"))
            values["detected_at"] = datetime.now(timezone.utc).isoformat()
            inserted = await self.repo.db.insert("assignments", values)
            assignment = inserted[0]
            await self.repo.db.insert("assignment_events", {
                "user_id": user_id, "assignment_id": assignment["id"], "event_type": "assignment.created",
                "processing_status": "pending",
            })
            return "created"
        assignment_id = existing["id"]
        if existing.get("content_hash") != fingerprint:
            values["workflow_status"] = existing.get("workflow_status") or "new"
            await self.repo.db.update("assignments", values, query={"id": f"eq.{assignment_id}", "user_id": f"eq.{user_id}"})
            for event in events:
                await self.repo.db.insert("assignment_events", {
                    "user_id": user_id, "assignment_id": assignment_id,
                    "event_type": f"assignment.{event['event_type']}",
                    "old_value": {"value": event["old_value"]}, "new_value": {"value": event["new_value"]},
                    "processing_status": "pending",
                })
            return "updated"
        return "unchanged"
