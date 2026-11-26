from fastapi import APIRouter, Depends, HTTPException
from app.core.clerk_auth import CurrentUser, get_current_user
from app.core.responses import success
from app.core.dependencies import get_supabase
from app.database.supabase_rest import SupabaseRestClient

router = APIRouter(prefix="/users", tags=["users"])


@router.get("/me")
async def me(user: CurrentUser = Depends(get_current_user)):
    return success({"clerk_user_id": user.user_id, "authenticated": True})


@router.get("/profile")
async def get_profile(user: CurrentUser = Depends(get_current_user), db: SupabaseRestClient = Depends(get_supabase)):
    rows = await db.select("profiles", query={"clerk_user_id": f"eq.{user.user_id}"}, limit=1)
    return success(rows[0] if rows else None)


@router.patch("/profile")
async def update_profile(payload: dict, user: CurrentUser = Depends(get_current_user), db: SupabaseRestClient = Depends(get_supabase)):
    allowed = {"full_name", "email", "college_name", "department", "course_name", "semester", "roll_number", "timezone", "onboarding_completed"}
    values = {k: v for k, v in payload.items() if k in allowed}
    if not values:
        raise HTTPException(400, "No editable profile fields supplied")
    existing = await db.select("profiles", query={"clerk_user_id": f"eq.{user.user_id}"}, limit=1)
    if existing:
        rows = await db.update("profiles", values, query={"clerk_user_id": f"eq.{user.user_id}"})
    else:
        rows = await db.insert("profiles", {"clerk_user_id": user.user_id, **values})
    return success(rows[0] if rows else values, "Profile saved")
