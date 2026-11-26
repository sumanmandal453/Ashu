from fastapi import APIRouter, Depends
from app.core.clerk_auth import CurrentUser, get_current_user
from app.core.dependencies import get_supabase
from app.core.responses import success
from app.database.supabase_rest import SupabaseRestClient

router = APIRouter(prefix="/subjects", tags=["subjects"])


@router.get("")
async def list_subjects(user: CurrentUser = Depends(get_current_user), db: SupabaseRestClient = Depends(get_supabase)):
    return success(await db.select("subjects", query={"user_id": f"eq.{user.user_id}"}, order="subject_name.asc", limit=500))
