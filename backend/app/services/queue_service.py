from app.core.config import settings
from app.database.admin import get_admin_client


async def enqueue_job(queue_name: str, job: dict) -> None:
    allowed = {"course-sync", "assignment-sync", "assignment-processing", "ai-generation", "document-generation", "notification-delivery", "deadline-reminders", "scheduled-dispatch"}
    if queue_name not in allowed:
        raise ValueError("Unknown queue")
    client = get_admin_client()
    try:
        await client.rpc("ashu_enqueue_job", {"queue_name": queue_name, "job": job})
    finally:
        await client.aclose()
