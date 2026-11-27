from __future__ import annotations

from datetime import datetime, timezone
from typing import Any

from app.core.config import settings
from app.database.repositories import Repository
from app.integrations.digiicampus.client import DigiiCampusClient
from app.integrations.digiicampus.normalizers import normalize_assignments, normalize_courses
from app.services.assignment_service import AssignmentService


def _items(payload: Any) -> list[dict[str, Any]]:
    if isinstance(payload, list):
        return [x for x in payload if isinstance(x, dict)]
    if isinstance(payload, dict):
        for key in ("data", "result", "results", "resources", "modules", "sessions", "events", "posts"):
            if isinstance(payload.get(key), list):
                return [x for x in payload[key] if isinstance(x, dict)]
    return []


async def sync_digiicampus(user_id: str, integration: dict[str, Any], db, *, client: DigiiCampusClient | None = None) -> dict[str, int]:
    if client is None:
        from app.services.integration_secrets import load_integration_credential

        auth_token = await load_integration_credential(
            db, str(integration["id"])
        )
        client = DigiiCampusClient(
            auth_token=auth_token,
            external_student_id=integration.get("external_student_id"),
        )
    assignment_service = AssignmentService(Repository(db, user_id))
    started = datetime.now(timezone.utc)
    counts = {"courses_found": 0, "assignments_found": 0, "assignments_created": 0, "assignments_updated": 0, "resources_found": 0}
    log_row = await db.insert("sync_logs", {"user_id": user_id, "integration_id": integration["id"], "sync_type": "digiicampus_readonly", "started_at": started.isoformat(), "sync_status": "running"})
    try:
        courses_payload = await client.get_courses()
        courses = normalize_courses(courses_payload)
        counts["courses_found"] = len(courses)
        course_map: dict[str, tuple[str, dict[str, Any]]] = {}
        for course in courses:
            external_class_id = course.get("external_class_id")
            if not external_class_id:
                continue
            existing = await db.select("courses", query={"user_id": f"eq.{user_id}", "integration_id": f"eq.{integration['id']}", "external_class_id": f"eq.{external_class_id}"}, limit=1)
            payload = {k: v for k, v in course.items() if k in {"external_course_id", "external_class_id", "course_name", "course_code", "faculty_name", "course_type", "course_status", "raw_source"}}
            payload.update({"user_id": user_id, "integration_id": integration["id"]})
            if existing:
                await db.update("courses", payload, query={"id": f"eq.{existing[0]['id']}", "user_id": f"eq.{user_id}"})
                course_id = existing[0]["id"]
            else:
                inserted = await db.insert("courses", payload)
                course_id = inserted[0]["id"]
            course_map[str(external_class_id)] = (course_id, course)

        for class_id, (course_id, course_data) in course_map.items():
            assignment_payload = await client.get_assignments(class_id)
            items = normalize_assignments(assignment_payload, class_id)
            counts["assignments_found"] += len(items)
            for item in items:
                item["external_class_id"] = class_id
                item["subject_name"] = course_data.get("course_name")
                # Fetch full detail only when the Bhawanipur detail path has been configured.
                detail_data = {}
                if settings.digii_assignment_detail_path:
                    detail = await client.get_assignment_details(item["external_assignment_id"], class_id)
                    details = normalize_assignments(detail, class_id)
                    if details:
                        detail_data = details[0]
                        for key in ("description", "instructions", "start_at", "deadline", "submission_type", "assignment_type", "grading_type", "total_marks", "portal_status"):
                            if detail_data.get(key) is not None:
                                item[key] = detail_data[key]
                result = await assignment_service.upsert_portal_assignment(integration["id"], course_id, user_id, item)
                if result == "created":
                    counts["assignments_created"] += 1
                elif result == "updated":
                    counts["assignments_updated"] += 1
                # Attachments are metadata-only until a verified, permitted download URL is available.
                attachment_source = (detail_data or {}).get("raw_source", {}) if detail_data else item.get("raw_source", {})
                attachment_list = attachment_source.get("attachments") or attachment_source.get("resources") or attachment_source.get("files") or []
                if isinstance(attachment_list, list):
                    existing_assignment = await db.select("assignments", query={"user_id": f"eq.{user_id}", "integration_id": f"eq.{integration['id']}", "external_class_id": f"eq.{class_id}", "external_assignment_id": f"eq.{item['external_assignment_id']}"}, limit=1)
                    if existing_assignment:
                        for attachment in attachment_list:
                            if not isinstance(attachment, dict):
                                continue
                            external_file_id = str(attachment.get("id") or attachment.get("resourceId") or attachment.get("fileId") or "")
                            filename = attachment.get("fileName") or attachment.get("name") or attachment.get("title")
                            if not filename:
                                continue
                            current = await db.select("assignment_attachments", query={"user_id": f"eq.{user_id}", "assignment_id": f"eq.{existing_assignment[0]['id']}", "original_file_name": f"eq.{filename}"}, limit=1)
                            values = {"user_id": user_id, "assignment_id": existing_assignment[0]["id"], "external_resource_id": external_file_id or None,
                                      "original_file_name": str(filename), "external_file_url": attachment.get("url") or attachment.get("fileUrl"),
                                      "file_type": attachment.get("fileType") or attachment.get("mimeType"), "extraction_status": "pending"}
                            if not current:
                                await db.insert("assignment_attachments", values)

        # Optional course modules, sessions and resources. Each remains disabled until its
        # endpoint path is independently verified against the Bhawanipur tenant.
        for class_id, (course_id, course_data) in course_map.items():
            if settings.digii_modules_path:
                module_payload = await client.get_course_modules(class_id)
                for index, module in enumerate(_items(module_payload)):
                    external_id = str(module.get("moduleId") or module.get("id") or "")
                    name = module.get("moduleName") or module.get("name") or module.get("title")
                    if not name:
                        continue
                    existing = await db.select("course_modules", query={"user_id": f"eq.{user_id}", "course_id": f"eq.{course_id}", "external_module_id": f"eq.{external_id}"}, limit=1) if external_id else []
                    values = {"user_id": user_id, "course_id": course_id, "external_module_id": external_id or None, "module_name": str(name), "module_order": index}
                    if existing:
                        await db.update("course_modules", values, query={"id": f"eq.{existing[0]['id']}", "user_id": f"eq.{user_id}"})
                    else:
                        await db.insert("course_modules", values)
            if settings.digii_sessions_path:
                session_payload = await client.get_course_sessions(class_id)
                for session in _items(session_payload):
                    external_id = str(session.get("sessionId") or session.get("id") or "")
                    title = session.get("sessionTitle") or session.get("title") or session.get("name")
                    if not title:
                        continue
                    existing = await db.select("course_sessions", query={"user_id": f"eq.{user_id}", "course_id": f"eq.{course_id}", "external_session_id": f"eq.{external_id}"}, limit=1) if external_id else []
                    values = {"user_id": user_id, "course_id": course_id, "external_session_id": external_id or None,
                              "session_title": str(title), "session_description": session.get("description"),
                              "session_status": session.get("status"), "faculty_name": session.get("facultyName")}
                    if existing:
                        await db.update("course_sessions", values, query={"id": f"eq.{existing[0]['id']}", "user_id": f"eq.{user_id}"})
                    else:
                        await db.insert("course_sessions", values)
            if settings.digii_resources_path:
                resource_payload = await client.get_resources(class_id)
                resources = _items(resource_payload)
                counts["resources_found"] += len(resources)
                for resource in resources:
                    external_id = str(resource.get("resourceId") or resource.get("id") or "")
                    name = resource.get("fileName") or resource.get("resourceName") or resource.get("name")
                    if not name:
                        continue
                    existing = await db.select("resources", query={"user_id": f"eq.{user_id}", "course_id": f"eq.{course_id}", "external_resource_id": f"eq.{external_id}"}, limit=1) if external_id else []
                    values = {"user_id": user_id, "course_id": course_id, "external_resource_id": external_id or None,
                              "resource_name": str(name), "external_resource_url": resource.get("fileUrl") or resource.get("url"),
                              "file_type": resource.get("fileType") or resource.get("mimeType")}
                    if existing:
                        await db.update("resources", values, query={"id": f"eq.{existing[0]['id']}", "user_id": f"eq.{user_id}"})
                    else:
                        await db.insert("resources", values)

        if settings.digii_feed_path:
            feed_payload = await client.get_feed()
            for post in _items(feed_payload):
                post_id = str(post.get("id") or post.get("postId") or "")
                text = post.get("text") or post.get("content") or post.get("description")
                if not text:
                    continue
                existing = await db.select("feed_posts", query={"user_id": f"eq.{user_id}", "integration_id": f"eq.{integration['id']}", "external_post_id": f"eq.{post_id}"}, limit=1) if post_id else []
                values = {"user_id": user_id, "integration_id": integration["id"], "external_post_id": post_id or None,
                          "author": post.get("authorName") or post.get("author"), "post_text": str(text),
                          "post_type": post.get("type"), "source_url": post.get("url")}
                if not existing:
                    await db.insert("feed_posts", values)
        if settings.digii_calendar_path:
            calendar_payload = await client.get_calendar_events()
            for event in _items(calendar_payload):
                event_id = str(event.get("id") or event.get("eventId") or "")
                title = event.get("title") or event.get("eventName") or event.get("name")
                if not title:
                    continue
                from app.integrations.digiicampus.normalizers import _parse_datetime
                existing = await db.select("calendar_events", query={"user_id": f"eq.{user_id}", "integration_id": f"eq.{integration['id']}", "external_event_id": f"eq.{event_id}"}, limit=1) if event_id else []
                values = {"user_id": user_id, "integration_id": integration["id"], "external_event_id": event_id or None,
                          "event_title": str(title), "event_type": event.get("type"),
                          "start_at": _parse_datetime(event.get("startDate") or event.get("startAt") or event.get("date")),
                          "end_at": _parse_datetime(event.get("endDate") or event.get("endAt")),
                          "venue": event.get("venue"), "faculty_name": event.get("facultyName"), "source": "digiicampus"}
                if existing:
                    await db.update("calendar_events", values, query={"id": f"eq.{existing[0]['id']}", "user_id": f"eq.{user_id}"})
                else:
                    await db.insert("calendar_events", values)
        if settings.digii_notifications_path:
            notifications_payload = await client.get_notifications()
            for note in _items(notifications_payload):
                note_id = str(note.get("id") or note.get("notificationId") or "")
                title = note.get("title") or note.get("message") or note.get("content")
                if not title:
                    continue
                existing = await db.select("portal_notifications", query={"user_id": f"eq.{user_id}", "integration_id": f"eq.{integration['id']}", "external_notification_id": f"eq.{note_id}"}, limit=1) if note_id else []
                if not existing:
                    await db.insert("portal_notifications", {"user_id": user_id, "integration_id": integration["id"],
                        "external_notification_id": note_id or None, "title": str(title), "body": note.get("description") or note.get("body"),
                        "is_read": bool(note.get("isRead", False))})

        completed = datetime.now(timezone.utc)
        await db.update("college_integrations", {"connection_status": "connected", "last_synced_at": completed.isoformat(), "last_error": None}, query={"id": f"eq.{integration['id']}", "user_id": f"eq.{user_id}"})
        if log_row:
            await db.update("sync_logs", {**counts, "completed_at": completed.isoformat(), "sync_status": "success"}, query={"id": f"eq.{log_row[0]['id']}"})
        return counts
    except Exception as exc:
        completed = datetime.now(timezone.utc)
        await db.update(
            "college_integrations",
            {"connection_status": "connection_error", "last_error": str(exc)[:500]},
            query={"id": f"eq.{integration['id']}", "user_id": f"eq.{user_id}"},
        )
        if log_row:
            await db.update(
                "sync_logs",
                {
                    "completed_at": completed.isoformat(),
                    "sync_status": "failed",
                    "error_message": str(exc)[:1000],
                    **counts,
                },
                query={"id": f"eq.{log_row[0]['id']}", "user_id": f"eq.{user_id}"},
            )
        raise
    finally:
        await client.aclose()
