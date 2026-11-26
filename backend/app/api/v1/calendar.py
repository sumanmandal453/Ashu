from datetime import datetime, timezone
from fastapi import APIRouter, Depends, Query
from app.core.clerk_auth import CurrentUser, get_current_user
from app.core.dependencies import get_supabase
from app.core.responses import success
from app.database.supabase_rest import SupabaseRestClient

router = APIRouter(prefix="/calendar", tags=["calendar"])


@router.get("/events")
async def events(start: str | None = None, end: str | None = None, user: CurrentUser = Depends(get_current_user), db: SupabaseRestClient = Depends(get_supabase)):
    query = {"user_id": f"eq.{user.user_id}"}
    if start: query["start_at"] = f"gte.{start}"
    if end: query["start_at"] = f"lte.{end}"
    return success(await db.select("calendar_events", query=query, order="start_at.asc", limit=1000))


@router.get("/upcoming")
async def upcoming(user: CurrentUser = Depends(get_current_user), db: SupabaseRestClient = Depends(get_supabase)):
    now = datetime.now(timezone.utc).isoformat()
    return success(await db.select("calendar_events", query={"user_id": f"eq.{user.user_id}", "start_at": f"gte.{now}"}, order="start_at.asc", limit=30))


@router.get("/monthly")
async def monthly(month: str = Query(..., description="YYYY-MM"), user: CurrentUser = Depends(get_current_user), db: SupabaseRestClient = Depends(get_supabase)):
    start = datetime.fromisoformat(month + "-01T00:00:00+00:00")
    if start.month == 12:
        end = start.replace(year=start.year + 1, month=1)
    else:
        end = start.replace(month=start.month + 1)
    rows = await db.select("calendar_events", query={"user_id": f"eq.{user.user_id}", "start_at": f"gte.{start.isoformat()}", "and": f"(start_at.lt.{end.isoformat()})"}, order="start_at.asc", limit=1000)
    return success(rows)


@router.get("/deadlines")
async def deadlines(user: CurrentUser = Depends(get_current_user), db: SupabaseRestClient = Depends(get_supabase)):
    return success(await db.select("assignments", query={"user_id": f"eq.{user.user_id}", "deadline": "not.is.null"}, order="deadline.asc", limit=500))
