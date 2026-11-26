from __future__ import annotations

import asyncio
import logging
from datetime import datetime, timezone
from typing import Any

import asyncpg

from app.core.config import settings
from app.database.admin import get_admin_client
from app.integrations.digiicampus.sync import sync_digiicampus
from app.services.ai_service import AIService
from app.services.queue_service import enqueue_job
from app.services.deadline_service import due_reminder_kinds
from app.workers.queue_consumer import PGMQConsumer

logger = logging.getLogger(__name__)
QUEUES = ["scheduled-dispatch", "course-sync", "assignment-sync", "assignment-processing", "ai-generation", "document-generation", "notification-delivery", "deadline-reminders"]


async def dispatch_sync_jobs() -> None:
    db = get_admin_client()
    try:
        integrations = await db.select("college_integrations", query={"provider": "eq.digiicampus", "connection_status": "eq.connected"}, limit=1000)
        for integration in integrations:
            await enqueue_job("assignment-sync", {
                "task_type": "integration.sync",
                "user_id": integration["user_id"],
                "integration_id": integration["id"],
            })
    finally:
        await db.aclose()


async def dispatch_due_reminders() -> None:
    """Create idempotent in-app reminders and enqueue configured Telegram alerts."""
    db = get_admin_client()
    try:
        assignments = await db.select(
            "assignments",
            query={"deadline": "not.is.null", "portal_is_submitted": "eq.false"},
            order="deadline.asc",
            limit=2000,
        )
        now = datetime.now(timezone.utc)
        for assignment in assignments:
            raw_deadline = assignment.get("deadline")
            if not raw_deadline:
                continue
            try:
                deadline = datetime.fromisoformat(str(raw_deadline).replace("Z", "+00:00"))
            except ValueError:
                continue
            reminder_kinds = due_reminder_kinds(deadline, now)
            if not reminder_kinds:
                continue
            user_id = assignment.get("user_id")
            if not user_id:
                continue
            preference_rows = await db.select(
                "notification_preferences", query={"user_id": f"eq.{user_id}"}, limit=1
            )
            preferences = preference_rows[0] if preference_rows else {}
            if preferences.get("deadline_reminder") is False:
                continue
            channels = await db.select(
                "notification_channels",
                query={"user_id": f"eq.{user_id}", "channel": "eq.telegram", "status": "eq.configured"},
                limit=10,
            )
            if preferences.get("telegram_enabled") is False and preference_rows:
                channels = []
            for kind in reminder_kinds:
                notification_type = f"deadline_reminder_{kind}"
                existing = await db.select(
                    "notifications",
                    query={
                        "user_id": f"eq.{user_id}",
                        "assignment_id": f"eq.{assignment['id']}",
                        "notification_type": f"eq.{notification_type}",
                    },
                    limit=1,
                )
                if existing:
                    continue
                label = kind.replace("_", " ")
                text = (
                    f"Your assignment '{assignment.get('title', 'Assignment')}' is due in {label}.\n"
                    f"Subject: {assignment.get('subject_name') or 'Not specified'}\n"
                    f"Deadline: {raw_deadline}"
                )
                try:
                    await db.insert("notifications", {
                        "user_id": user_id,
                        "assignment_id": assignment["id"],
                        "notification_type": notification_type,
                        "title": f"Assignment deadline in {label}",
                        "message": text,
                        "channel": "in_app",
                        "delivery_status": "sent",
                        "sent_at": now.isoformat(),
                    })
                except Exception:
                    # A concurrent dispatch may have inserted the same reminder.
                    logger.info("Reminder already created user=%s assignment=%s kind=%s", user_id, assignment["id"], kind)
                    continue
                for channel in channels:
                    await db.rpc("ashu_enqueue_job", {
                        "queue_name": "notification-delivery",
                        "job": {
                            "task_type": "notification.telegram",
                            "user_id": user_id,
                            "chat_id": channel["recipient"],
                            "text": f"ASHU - DEADLINE REMINDER\n\n{text}",
                        },
                    })
    finally:
        await db.aclose()


async def process_job(message: dict[str, Any]) -> None:
    task_type = message.get("task_type")
    user_id = message.get("user_id")
    if task_type == "dispatch.sync":
        await dispatch_sync_jobs()
        await dispatch_due_reminders()
        return
    if task_type == "dispatch.reminders":
        await dispatch_due_reminders()
        return
    if task_type == "integration.sync":
        db = get_admin_client()
        try:
            rows = await db.select("college_integrations", query={"id": f"eq.{message['integration_id']}", "user_id": f"eq.{user_id}"}, limit=1)
            if not rows:
                logger.warning("Integration job references missing integration")
                return
            counts = await sync_digiicampus(user_id, rows[0], db)
            if counts.get("assignments_created", 0):
                recent = await db.select("assignments", query={"user_id": f"eq.{user_id}", "integration_id": f"eq.{rows[0]['id']}"}, order="detected_at.desc", limit=counts["assignments_created"])
                for assignment in recent:
                    await db.rpc("ashu_enqueue_job", {"queue_name": "assignment-processing", "job": {"task_type": "assignment.process", "user_id": user_id, "assignment_id": assignment["id"]}})
        finally:
            await db.aclose()
        return
    if task_type == "assignment.process":
        db = get_admin_client()
        try:
            rows = await db.select("assignments", query={"id": f"eq.{message['assignment_id']}", "user_id": f"eq.{user_id}"}, limit=1)
            if not rows:
                return
            assignment = rows[0]
            source_texts = []
            from app.documents.extract import extract_text
            attachments = await db.select("assignment_attachments", query={"assignment_id": f"eq.{message['assignment_id']}", "user_id": f"eq.{user_id}"}, limit=100)
            for attachment in attachments:
                storage_path = attachment.get("storage_path")
                if not storage_path:
                    continue  # External portal files are not fetched until their download host/auth are verified.
                raw_file = await db.download("assignment-files", storage_path)
                try:
                    extracted = extract_text(attachment.get("original_file_name", "attachment.pdf"), raw_file)
                    source_texts.append({"file_name": attachment.get("original_file_name"), "text": extracted[:30000]})
                    await db.update("assignment_attachments", {"extraction_status": "processed"}, query={"id": f"eq.{attachment['id']}", "user_id": f"eq.{user_id}"})
                except Exception as exc:
                    await db.update("assignment_attachments", {"extraction_status": "failed"}, query={"id": f"eq.{attachment['id']}", "user_id": f"eq.{user_id}"})
                    logger.warning("Could not extract assignment attachment id=%s: %s", attachment.get("id"), exc)
            summary = await AIService().summarize_assignment(assignment, source_texts)
            questions = summary.pop("questions", []) or []
            existing_summaries = await db.select("assignment_summaries", query={"user_id": f"eq.{user_id}", "assignment_id": f"eq.{message['assignment_id']}"}, order="generated_at.desc", limit=1)
            summary_values = {"user_id": user_id, "assignment_id": message["assignment_id"], **summary, "ai_provider": "gemini"}
            if existing_summaries:
                await db.update("assignment_summaries", summary_values, query={"id": f"eq.{existing_summaries[0]['id']}", "user_id": f"eq.{user_id}"})
            else:
                await db.insert("assignment_summaries", summary_values)
            for index, question in enumerate(questions, 1):
                if not isinstance(question, dict) or not str(question.get("question_text", "")).strip():
                    continue
                qnum = int(question.get("question_number") or index)
                existing_question = await db.select("assignment_questions", query={"user_id": f"eq.{user_id}", "assignment_id": f"eq.{message['assignment_id']}", "question_number": f"eq.{qnum}"}, limit=1)
                q_values = {"user_id": user_id, "assignment_id": message["assignment_id"], "question_number": qnum,
                            "question_text": str(question["question_text"]), "maximum_marks": question.get("maximum_marks"),
                            "question_type": question.get("question_type"), "source_reference": {"origin": "assignment_analysis"}}
                if existing_question:
                    await db.update("assignment_questions", q_values, query={"id": f"eq.{existing_question[0]['id']}", "user_id": f"eq.{user_id}"})
                else:
                    await db.insert("assignment_questions", q_values)
            await db.update("assignments", {"workflow_status": "ai_generated"}, query={"id": f"eq.{message['assignment_id']}", "user_id": f"eq.{user_id}"})
            note_text = summary.get("short_summary") or "A new assignment was detected in your college portal."
            existing_note = await db.select("notifications", query={"user_id": f"eq.{user_id}", "assignment_id": f"eq.{message['assignment_id']}", "notification_type": "eq.assignment_summary", "channel": "eq.in_app"}, limit=1)
            if not existing_note:
                await db.insert("notifications", {
                    "user_id": user_id, "assignment_id": message["assignment_id"],
                    "notification_type": "assignment_summary", "title": f"New assignment: {assignment.get('title', 'Assignment')}",
                    "message": note_text, "channel": "in_app", "delivery_status": "sent",
                })
            channels = await db.select("notification_channels", query={"user_id": f"eq.{user_id}", "channel": "eq.telegram", "status": "eq.configured"}, limit=5)
            for channel in channels:
                await db.rpc("ashu_enqueue_job", {"queue_name": "notification-delivery", "job": {
                    "task_type": "notification.telegram", "user_id": user_id, "chat_id": channel["recipient"],
                    "text": f"ASHU - NEW ASSIGNMENT\n\n{assignment.get('title', 'Assignment')}\n\n{note_text}\n\nDeadline: {assignment.get('deadline') or 'Not provided'}"
                }})
        finally:
            await db.aclose()
        return
    if task_type == "material.ingest":
        from app.ai.rag.ingestion import ingest_document
        db = get_admin_client()
        try:
            rows = await db.select("study_materials", query={"id": f"eq.{message['material_id']}", "user_id": f"eq.{user_id}"}, limit=1)
            if not rows:
                return
            material = rows[0]
            raw = await db.download("study-materials", material["storage_path"])
            chunks = await ingest_document(material["file_name"], raw)
            if chunks:
                for chunk in chunks:
                    await db.insert("material_chunks", {"user_id": user_id, "material_id": material["id"], **chunk})
            await db.update("study_materials", {"processing_status": "processed"}, query={"id": f"eq.{material['id']}", "user_id": f"eq.{user_id}"})
        except Exception as exc:
            await db.update("study_materials", {"processing_status": "failed"}, query={"id": f"eq.{message['material_id']}", "user_id": f"eq.{user_id}"})
            raise exc
        finally:
            await db.aclose()
        return
    if task_type == "notification.telegram":
        from app.integrations.telegram import TelegramClient
        await TelegramClient().send_message(message["chat_id"], message["text"])
        return
    if task_type == "notification.whatsapp":
        from app.integrations.whatsapp import WhatsAppClient
        await WhatsAppClient().send_template(message["phone"], message["template_name"], message.get("language", "en_US"))
        return
    raise ValueError(f"Unknown worker task type: {task_type!r}")


async def run_worker() -> None:
    if not settings.supabase_database_url:
        raise RuntimeError("SUPABASE_DATABASE_URL is required for the Python worker")
    pool = await asyncpg.create_pool(settings.supabase_database_url, min_size=1, max_size=5, ssl="require")
    consumer = PGMQConsumer(pool)
    logger.info("Ashu background worker started")
    try:
        while True:
            had_work = False
            for queue_name in QUEUES:
                try:
                    messages = await consumer.read(queue_name)
                except Exception:
                    logger.exception("Failed reading queue %s", queue_name)
                    continue
                for message in messages:
                    had_work = True
                    msg_id = int(message["msg_id"])
                    payload = message.get("message") or {}
                    try:
                        await process_job(payload)
                        await consumer.archive(queue_name, msg_id)
                    except Exception as exc:
                        logger.exception("Job failed queue=%s msg_id=%s", queue_name, msg_id)
                        read_count = int(message.get("read_ct") or 1)
                        if read_count >= 5:
                            try:
                                admin = get_admin_client()
                                try:
                                    await admin.insert("worker_failures", {"queue_name": queue_name, "message_id": msg_id,
                                        "user_id": payload.get("user_id"), "payload": payload, "attempts": read_count,
                                        "error_message": str(exc)[:2000]})
                                finally:
                                    await admin.aclose()
                                await consumer.archive(queue_name, msg_id)
                            except Exception:
                                logger.exception("Could not archive exhausted job queue=%s msg_id=%s", queue_name, msg_id)
                        # Under five attempts, leave unarchived so PGMQ redelivers after visibility timeout.
            if not had_work:
                await asyncio.sleep(settings.worker_poll_seconds)
    finally:
        await pool.close()


if __name__ == "__main__":
    logging.basicConfig(level=settings.log_level)
    asyncio.run(run_worker())
