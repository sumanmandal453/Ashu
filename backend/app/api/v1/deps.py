from fastapi import Depends
from app.core.clerk_auth import CurrentUser, get_current_user
from app.core.dependencies import get_supabase
from app.database.supabase_rest import SupabaseRestClient


def current_user(user: CurrentUser = Depends(get_current_user)) -> CurrentUser:
    return user


def supabase(db: SupabaseRestClient = Depends(get_supabase)) -> SupabaseRestClient:
    return db
