from fastapi import APIRouter, Depends
from app.core.clerk_auth import CurrentUser, get_current_user
from app.core.dependencies import get_supabase
from app.core.responses import success
from app.database.supabase_rest import SupabaseRestClient
from app.services.analytics_service import assignment_analytics, weekly_completion

router = APIRouter(prefix="/dashboard", tags=["dashboard"])


@router.get("/summary")
async def summary(user: CurrentUser = Depends(get_current_user), db: SupabaseRestClient = Depends(get_supabase)):
    assignments = await db.select("assignments", query={"user_id": f"eq.{user.user_id}"}, limit=1000)
    return success(assignment_analytics(assignments))


@router.get("/upcoming-deadlines")
async def upcoming(user: CurrentUser = Depends(get_current_user), db: SupabaseRestClient = Depends(get_supabase)):
    rows = await db.select("assignments", query={"user_id": f"eq.{user.user_id}", "deadline": "not.is.null", "portal_is_submitted": "not.is.true"}, order="deadline.asc", limit=10)
    return success(rows)


@router.get("/recent-activity")
async def recent(user: CurrentUser = Depends(get_current_user), db: SupabaseRestClient = Depends(get_supabase)):
    rows = await db.select("assignment_events", query={"user_id": f"eq.{user.user_id}"}, order="event_timestamp.desc", limit=15)
    return success(rows)


@router.get("/completed-per-week")
async def completed(user: CurrentUser = Depends(get_current_user), db: SupabaseRestClient = Depends(get_supabase)):
    rows = await db.select("submission_attempts", query={"user_id": f"eq.{user.user_id}", "submission_status": "eq.submitted"}, order="verified_at.desc", limit=1000)
    return success(weekly_completion(rows, weeks=6))


@router.get("/assignments-by-subject")
async def by_subject(user: CurrentUser = Depends(get_current_user), db: SupabaseRestClient = Depends(get_supabase)):
    rows = await db.select("assignments", query={"user_id": f"eq.{user.user_id}"}, limit=1000)
    return success(assignment_analytics(rows)["by_subject"])
