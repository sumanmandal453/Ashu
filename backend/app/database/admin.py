from app.core.config import settings
from app.database.supabase_rest import SupabaseRestClient


def get_admin_client() -> SupabaseRestClient:
    if not settings.supabase_url or not settings.supabase_secret_key:
        raise RuntimeError("Supabase server-side secret key is not configured")
    return SupabaseRestClient(settings.supabase_url, settings.supabase_secret_key)
