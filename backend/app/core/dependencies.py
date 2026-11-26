from collections.abc import AsyncIterator

from fastapi import Depends, HTTPException, Request

from app.core.clerk_auth import CurrentUser, get_current_user
from app.core.config import settings
from app.database.supabase_rest import SupabaseRestClient


async def get_supabase(
    request: Request,
    user: CurrentUser = Depends(get_current_user),
) -> AsyncIterator[SupabaseRestClient]:
    if not settings.supabase_url or not settings.supabase_publishable_key:
        raise HTTPException(503, "Supabase is not configured")
    authorization = request.headers.get("authorization", "")
    token = authorization.removeprefix("Bearer ").strip()
    if not token:
        raise HTTPException(401, "A Clerk session token is required")
    client = SupabaseRestClient(
        base_url=settings.supabase_url,
        api_key=settings.supabase_publishable_key,
        access_token=token,
    )
    try:
        # Provision the user's profile on first authenticated backend access.
        # This satisfies profile foreign keys even if the Clerk webhook has not
        # arrived yet. The Clerk JWT is still the identity source and RLS applies.
        profiles = await client.select(
            "profiles",
            query={"clerk_user_id": f"eq.{user.user_id}"},
            limit=1,
        )
        if not profiles:
            claims = user.claims
            full_name = claims.get("name")
            if not full_name:
                full_name = " ".join(
                    part for part in (claims.get("given_name"), claims.get("family_name")) if part
                ) or None
            email = claims.get("email") or claims.get("email_address")
            await client.insert(
                "profiles",
                {
                    "clerk_user_id": user.user_id,
                    "full_name": full_name,
                    "email": email,
                    "college_name": "Bhawanipur Global Campus",
                    "timezone": "Asia/Kolkata",
                },
            )
        yield client
    finally:
        await client.aclose()
