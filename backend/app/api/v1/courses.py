from fastapi import APIRouter, Depends, HTTPException
from app.core.clerk_auth import CurrentUser, get_current_user
from app.core.dependencies import get_supabase
from app.core.responses import success
from app.database.supabase_rest import SupabaseRestClient

router = APIRouter(prefix="/courses", tags=["courses"])


@router.get("")
async def list_courses(user: CurrentUser = Depends(get_current_user), db: SupabaseRestClient = Depends(get_supabase)):
    rows = await db.select("courses", query={"user_id": f"eq.{user.user_id}"}, order="course_name.asc", limit=500)
    return success(rows)


@router.get("/{course_id}")
async def get_course(course_id: str, user: CurrentUser = Depends(get_current_user), db: SupabaseRestClient = Depends(get_supabase)):
    rows = await db.select("courses", query={"id": f"eq.{course_id}", "user_id": f"eq.{user.user_id}"}, limit=1)
    if not rows:
        raise HTTPException(404, "Course not found")
    return success(rows[0])


@router.get("/{course_id}/modules")
async def modules(course_id: str, user: CurrentUser = Depends(get_current_user), db: SupabaseRestClient = Depends(get_supabase)):
    rows = await db.select("courses", query={"id": f"eq.{course_id}", "user_id": f"eq.{user.user_id}"}, limit=1)
    if not rows:
        raise HTTPException(404, "Course not found")
    return success(await db.select("course_modules", query={"course_id": f"eq.{course_id}", "user_id": f"eq.{user.user_id}"}, order="module_order.asc", limit=500))


@router.get("/{course_id}/sessions")
async def sessions(course_id: str, user: CurrentUser = Depends(get_current_user), db: SupabaseRestClient = Depends(get_supabase)):
    rows = await db.select("courses", query={"id": f"eq.{course_id}", "user_id": f"eq.{user.user_id}"}, limit=1)
    if not rows:
        raise HTTPException(404, "Course not found")
    return success(await db.select("course_sessions", query={"course_id": f"eq.{course_id}", "user_id": f"eq.{user.user_id}"}, order="session_date.asc", limit=1000))


@router.get("/{course_id}/resources")
async def resources(course_id: str, user: CurrentUser = Depends(get_current_user), db: SupabaseRestClient = Depends(get_supabase)):
    rows = await db.select("courses", query={"id": f"eq.{course_id}", "user_id": f"eq.{user.user_id}"}, limit=1)
    if not rows:
        raise HTTPException(404, "Course not found")
    rows = await db.select("resources", query={"course_id": f"eq.{course_id}", "user_id": f"eq.{user.user_id}"}, limit=1000)
    for row in rows:
        if row.get("storage_path"):
            row["download_url"] = await db.signed_url("study-materials", row["storage_path"])
    return success(rows)
