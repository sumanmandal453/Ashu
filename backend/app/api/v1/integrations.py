from fastapi import APIRouter, Depends, HTTPException
from app.core.clerk_auth import CurrentUser, get_current_user
from app.core.config import settings
from app.core.dependencies import get_supabase
from app.core.exceptions import IntegrationUnavailable
from app.core.responses import success
from app.database.supabase_rest import SupabaseRestClient
from app.database.admin import get_admin_client
from app.services.integration_secrets import (
    delete_integration_credential,
    load_integration_credential,
)
from app.integrations.digiicampus.client import DigiiCampusClient
from app.integrations.digiicampus.sync import sync_digiicampus
from app.services.queue_service import enqueue_job
from app.schemas.integrations import TelegramConnectRequest, WhatsAppConnectRequest

router = APIRouter(prefix="/integrations", tags=["integrations"])


@router.get("")
async def list_integrations(user: CurrentUser = Depends(get_current_user), db: SupabaseRestClient = Depends(get_supabase)):
    rows = await db.select("college_integrations", query={"user_id": f"eq.{user.user_id}"}, limit=30)
    return success(rows)


@router.post("/digii/connect")
async def connect_digii(user: CurrentUser = Depends(get_current_user), db: SupabaseRestClient = Depends(get_supabase)):
    existing = await db.select("college_integrations", query={"user_id": f"eq.{user.user_id}", "provider": "eq.digiicampus"}, limit=1)
    values = {"provider": "digiicampus", "tenant_name": "Bhawanipur Global Campus", "base_url": settings.digii_base_url,
              "connection_status": "authentication_required", "permission_status": "not_verified"}
    if existing:
        rows = await db.update("college_integrations", values, query={"id": f"eq.{existing[0]['id']}", "user_id": f"eq.{user.user_id}"})
        row = rows[0] if rows else existing[0]
    else:
        rows = await db.insert("college_integrations", {"user_id": user.user_id, **values})
        row = rows[0] if rows else values
    return success(row, "Integration record created. Complete an authorized portal connection before syncing.")


@router.post("/digii/test")
async def test_digii(user: CurrentUser = Depends(get_current_user), db: SupabaseRestClient = Depends(get_supabase)):
    rows = await db.select("college_integrations", query={"user_id": f"eq.{user.user_id}", "provider": "eq.digiicampus"}, limit=1)
    if not rows:
        raise HTTPException(404, "Connect Digiicampus first")
    if not settings.digii_readonly_enabled:
        raise HTTPException(503, "Digiicampus connector is disabled pending Bhawanipur endpoint and authorization verification")
    admin = get_admin_client()
    try:
        auth_token = await load_integration_credential(
            admin, rows[0]["id"]
        )
    finally:
        await admin.aclose()
    client = DigiiCampusClient(auth_token=auth_token, external_student_id=rows[0].get("external_student_id"))
    try:
        result = await client.test_connection()
        await db.update("college_integrations", {"connection_status": "connected", "permission_status": "verified"}, query={"id": f"eq.{rows[0]['id']}", "user_id": f"eq.{user.user_id}"})
        return success({"connected": True, "profile": result.get("profile")}, "Digiicampus read-only connection verified")
    except IntegrationUnavailable as exc:
        await db.update("college_integrations", {"connection_status": "connection_error", "last_error": str(exc)}, query={"id": f"eq.{rows[0]['id']}", "user_id": f"eq.{user.user_id}"})
        raise HTTPException(503, str(exc)) from exc
    finally:
        await client.aclose()


@router.post("/digii/sync")
async def sync_digii(user: CurrentUser = Depends(get_current_user), db: SupabaseRestClient = Depends(get_supabase)):
    rows = await db.select("college_integrations", query={"user_id": f"eq.{user.user_id}", "provider": "eq.digiicampus"}, limit=1)
    if not rows:
        raise HTTPException(404, "Connect Digiicampus first")
    if not settings.digii_readonly_enabled:
        raise HTTPException(503, "Digiicampus read-only integration is disabled")
    await enqueue_job("assignment-sync", {"task_type": "integration.sync", "user_id": user.user_id, "integration_id": rows[0]["id"]})
    return success({"queued": True, "integration_id": rows[0]["id"]}, "Digiicampus synchronization queued")


@router.get("/digii/status")
async def digii_status(user: CurrentUser = Depends(get_current_user), db: SupabaseRestClient = Depends(get_supabase)):
    rows = await db.select("college_integrations", query={"user_id": f"eq.{user.user_id}", "provider": "eq.digiicampus"}, limit=1)
    row = rows[0] if rows else {"connection_status": "not_connected"}
    return success(row)


@router.get("/digii/courses")
async def digii_courses(user: CurrentUser = Depends(get_current_user), db: SupabaseRestClient = Depends(get_supabase)):
    rows = await db.select("courses", query={"user_id": f"eq.{user.user_id}"}, order="course_name.asc", limit=500)
    return success(rows)


@router.get("/digii/feed")
async def digii_feed(user: CurrentUser = Depends(get_current_user), db: SupabaseRestClient = Depends(get_supabase)):
    rows = await db.select("feed_posts", query={"user_id": f"eq.{user.user_id}"}, order="posted_at.desc", limit=100)
    return success(rows)


@router.get("/digii/notifications")
async def digii_notifications(user: CurrentUser = Depends(get_current_user), db: SupabaseRestClient = Depends(get_supabase)):
    rows = await db.select("portal_notifications", query={"user_id": f"eq.{user.user_id}"}, order="created_at.desc", limit=100)
    return success(rows)


@router.delete("/digii/disconnect")
async def disconnect_digii(user: CurrentUser = Depends(get_current_user), db: SupabaseRestClient = Depends(get_supabase)):
    rows = await db.select(
        "college_integrations",
        query={
            "user_id": f"eq.{user.user_id}",
            "provider": "eq.digiicampus",
        },
        select="id",
        limit=1,
    )

    if rows:
        admin = get_admin_client()
        try:
            await delete_integration_credential(admin, rows[0]["id"])
        finally:
            await admin.aclose()

    await db.update(
        "college_integrations",
        {"connection_status": "disconnected"},
        query={
            "user_id": f"eq.{user.user_id}",
            "provider": "eq.digiicampus",
        },
    )
    return success({"disconnected": True})


@router.post("/telegram/connect")
async def connect_telegram(payload: TelegramConnectRequest, user: CurrentUser = Depends(get_current_user), db: SupabaseRestClient = Depends(get_supabase)):
    rows = await db.insert("notification_channels", {"user_id": user.user_id, "channel": "telegram", "recipient": payload.chat_id, "status": "configured"})
    return success(rows[0] if rows else {}, "Telegram destination saved")


@router.post("/telegram/test")
async def test_telegram(user: CurrentUser = Depends(get_current_user), db: SupabaseRestClient = Depends(get_supabase)):
    from app.integrations.telegram import TelegramClient
    rows = await db.select("notification_channels", query={"user_id": f"eq.{user.user_id}", "channel": "eq.telegram", "status": "eq.configured"}, limit=1)
    if not rows:
        raise HTTPException(404, "Configure a Telegram chat ID first")
    result = await TelegramClient().send_message(rows[0]["recipient"], "Ashu Telegram connection test successful.")
    return success({"message_id": result.get("message_id")}, "Telegram test sent")


@router.post("/whatsapp/connect")
async def connect_whatsapp(payload: WhatsAppConnectRequest, user: CurrentUser = Depends(get_current_user), db: SupabaseRestClient = Depends(get_supabase)):
    from datetime import datetime, timezone
    rows = await db.insert("notification_channels", {"user_id": user.user_id, "channel": "whatsapp", "recipient": payload.phone_number, "status": "configured", "consent_at": datetime.now(timezone.utc).isoformat()})
    return success(rows[0] if rows else {}, "WhatsApp recipient saved. Ensure the user has opted in and the required template is approved.")


@router.post("/whatsapp/test")
async def test_whatsapp(template_name: str, user: CurrentUser = Depends(get_current_user), db: SupabaseRestClient = Depends(get_supabase)):
    from app.integrations.whatsapp import WhatsAppClient
    rows = await db.select("notification_channels", query={"user_id": f"eq.{user.user_id}", "channel": "eq.whatsapp", "status": "eq.configured"}, limit=1)
    if not rows:
        raise HTTPException(404, "Configure a WhatsApp recipient first")
    if not rows[0].get("consent_at"):
        raise HTTPException(409, "WhatsApp recipient consent is required")
    result = await WhatsAppClient().send_template(rows[0]["recipient"], template_name)
    return success(result, "WhatsApp template request accepted")
