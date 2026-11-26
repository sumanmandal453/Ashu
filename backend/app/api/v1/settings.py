from fastapi import APIRouter, Depends
from app.core.clerk_auth import CurrentUser, get_current_user
from app.core.dependencies import get_supabase
from app.core.responses import success
from app.database.supabase_rest import SupabaseRestClient

router = APIRouter(prefix="/settings", tags=["settings"])


@router.get("")
async def get_settings(user: CurrentUser = Depends(get_current_user), db: SupabaseRestClient = Depends(get_supabase)):
    profile = await db.select("profiles", query={"clerk_user_id": f"eq.{user.user_id}"}, limit=1)
    preferences = await db.select("notification_preferences", query={"user_id": f"eq.{user.user_id}"}, limit=1)
    return success({"profile": profile[0] if profile else {}, "notifications": preferences[0] if preferences else {}})


@router.patch("/profile")
async def patch_profile(payload: dict, user: CurrentUser = Depends(get_current_user), db: SupabaseRestClient = Depends(get_supabase)):
    allowed = {"full_name", "email", "college_name", "department", "course_name", "semester", "roll_number", "timezone", "onboarding_completed"}
    values = {k: v for k, v in payload.items() if k in allowed}
    existing = await db.select("profiles", query={"clerk_user_id": f"eq.{user.user_id}"}, limit=1)
    rows = await db.update("profiles", values, query={"clerk_user_id": f"eq.{user.user_id}"}) if existing else await db.insert("profiles", {"clerk_user_id": user.user_id, **values})
    return success(rows[0] if rows else values)


@router.patch("/preferences")
async def patch_preferences(payload: dict, user: CurrentUser = Depends(get_current_user), db: SupabaseRestClient = Depends(get_supabase)):
    allowed = {"telegram_enabled", "whatsapp_enabled", "new_assignment_alert", "deadline_reminder", "answer_ready", "document_ready", "approval_required", "submission_confirmation", "quiet_hours_start", "quiet_hours_end"}
    values = {k: v for k, v in payload.items() if k in allowed}
    existing = await db.select("notification_preferences", query={"user_id": f"eq.{user.user_id}"}, limit=1)
    rows = await db.update("notification_preferences", values, query={"user_id": f"eq.{user.user_id}"}) if existing else await db.insert("notification_preferences", {"user_id": user.user_id, **values})
    return success(rows[0] if rows else values)


@router.patch("/ai-preferences")
async def ai_preferences(payload: dict, user: CurrentUser = Depends(get_current_user), db: SupabaseRestClient = Depends(get_supabase)):
    allowed = {"default_language", "default_answer_length", "default_answer_style", "default_ai_provider"}
    values = {k: v for k, v in payload.items() if k in allowed}
    existing = await db.select("user_preferences", query={"user_id": f"eq.{user.user_id}"}, limit=1)
    rows = await db.update("user_preferences", values, query={"user_id": f"eq.{user.user_id}"}) if existing else await db.insert("user_preferences", {"user_id": user.user_id, **values})
    return success(rows[0] if rows else values)


@router.patch("/reminders")
async def reminders(payload: dict, user: CurrentUser = Depends(get_current_user), db: SupabaseRestClient = Depends(get_supabase)):
    allowed = {"reminder_offsets", "timezone", "quiet_hours_start", "quiet_hours_end"}
    values = {k: v for k, v in payload.items() if k in allowed}
    existing = await db.select("user_preferences", query={"user_id": f"eq.{user.user_id}"}, limit=1)
    rows = await db.update("user_preferences", values, query={"user_id": f"eq.{user.user_id}"}) if existing else await db.insert("user_preferences", {"user_id": user.user_id, **values})
    return success(rows[0] if rows else values)
