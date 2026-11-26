from fastapi import APIRouter, Depends
from app.core.clerk_auth import CurrentUser, get_current_user
from app.core.dependencies import get_supabase
from app.core.responses import success
from app.database.supabase_rest import SupabaseRestClient
from app.services.analytics_service import assignment_analytics, weekly_completion

router = APIRouter(prefix="/analytics", tags=["analytics"])


async def _rows(user, db):
    return await db.select("assignments", query={"user_id": f"eq.{user.user_id}"}, limit=2000)


@router.get("/overview")
async def overview(user: CurrentUser = Depends(get_current_user), db: SupabaseRestClient = Depends(get_supabase)):
    return success(assignment_analytics(await _rows(user, db)))


@router.get("/weekly-completion")
async def weekly(user: CurrentUser = Depends(get_current_user), db: SupabaseRestClient = Depends(get_supabase)):
    rows = await db.select("submission_attempts", query={"user_id": f"eq.{user.user_id}", "submission_status": "eq.submitted"}, order="verified_at.desc", limit=500)
    return success(weekly_completion(rows, weeks=6))


@router.get("/subject-distribution")
async def subjects(user: CurrentUser = Depends(get_current_user), db: SupabaseRestClient = Depends(get_supabase)):
    return success(assignment_analytics(await _rows(user, db))["by_subject"])


@router.get("/submission-performance")
async def submission_performance(user: CurrentUser = Depends(get_current_user), db: SupabaseRestClient = Depends(get_supabase)):
    rows = await db.select("submission_attempts", query={"user_id": f"eq.{user.user_id}"}, limit=1000)
    submitted = [r for r in rows if r.get("submission_status") == "submitted"]
    failed = [r for r in rows if r.get("submission_status") == "failed"]
    return success({"total_attempts": len(rows), "verified_submissions": len(submitted), "failed_attempts": len(failed)})
