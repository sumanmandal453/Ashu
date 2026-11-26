from datetime import datetime, timezone
from fastapi import APIRouter, Depends, HTTPException
from app.core.clerk_auth import CurrentUser, get_current_user
from app.core.dependencies import get_supabase
from app.core.responses import success
from app.database.supabase_rest import SupabaseRestClient

router = APIRouter(prefix="/notifications", tags=["notifications"])


@router.get("")
async def list_notifications(user: CurrentUser = Depends(get_current_user), db: SupabaseRestClient = Depends(get_supabase)):
    rows = await db.select("notifications", query={"user_id": f"eq.{user.user_id}"}, order="created_at.desc", limit=200)
    return success(rows)


@router.patch("/{notification_id}/read")
async def mark_read(notification_id: str, user: CurrentUser = Depends(get_current_user), db: SupabaseRestClient = Depends(get_supabase)):
    rows = await db.update("notifications", {"read_at": datetime.now(timezone.utc).isoformat()}, query={"id": f"eq.{notification_id}", "user_id": f"eq.{user.user_id}"})
    if not rows:
        raise HTTPException(404, "Notification not found")
    return success(rows[0])


@router.patch("/read-all")
async def read_all(user: CurrentUser = Depends(get_current_user), db: SupabaseRestClient = Depends(get_supabase)):
    rows = await db.update("notifications", {"read_at": datetime.now(timezone.utc).isoformat()}, query={"user_id": f"eq.{user.user_id}", "read_at": "is.null"})
    return success({"updated": len(rows)})


@router.get("/preferences")
async def get_preferences(user: CurrentUser = Depends(get_current_user), db: SupabaseRestClient = Depends(get_supabase)):
    rows = await db.select("notification_preferences", query={"user_id": f"eq.{user.user_id}"}, limit=1)
    return success(rows[0] if rows else {})


@router.patch("/preferences")
async def update_preferences(payload: dict, user: CurrentUser = Depends(get_current_user), db: SupabaseRestClient = Depends(get_supabase)):
    allowed = {"telegram_enabled", "whatsapp_enabled", "new_assignment_alert", "deadline_reminder", "answer_ready", "document_ready", "approval_required", "submission_confirmation", "quiet_hours_start", "quiet_hours_end"}
    values = {k: v for k, v in payload.items() if k in allowed}
    existing = await db.select("notification_preferences", query={"user_id": f"eq.{user.user_id}"}, limit=1)
    if existing:
        rows = await db.update("notification_preferences", values, query={"user_id": f"eq.{user.user_id}"})
    else:
        rows = await db.insert("notification_preferences", {"user_id": user.user_id, **values})
    return success(rows[0] if rows else values)
