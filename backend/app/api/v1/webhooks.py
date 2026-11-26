from fastapi import APIRouter, HTTPException, Request
from app.core.config import settings
from app.database.admin import get_admin_client

router = APIRouter(prefix="/webhooks", tags=["webhooks"])


@router.post("/clerk")
async def clerk_webhook(request: Request):
    if not settings.clerk_webhook_signing_secret:
        raise HTTPException(503, "Clerk webhook verification is not configured")
    body = await request.body()
    headers = {k.lower(): v for k, v in request.headers.items() if k.lower().startswith("svix-")}
    try:
        from svix.webhooks import Webhook
        event = Webhook(settings.clerk_webhook_signing_secret).verify(body, headers)
    except Exception as exc:
        raise HTTPException(400, "Invalid Clerk webhook signature") from exc
    event_type = event.get("type")
    data = event.get("data", {})
    user_id = data.get("id")
    if not user_id:
        return {"received": True, "ignored": True}
    db = get_admin_client()
    try:
        if event_type in {"user.created", "user.updated"}:
            emails = data.get("email_addresses", [])
            primary_id = data.get("primary_email_address_id")
            primary_email = next((x.get("email_address") for x in emails if x.get("id") == primary_id), None)
            values = {"clerk_user_id": user_id, "full_name": " ".join(x for x in [data.get("first_name"), data.get("last_name")] if x), "email": primary_email}
            await db.rpc("ashu_upsert_profile", {"profile": values})
        elif event_type == "user.deleted":
            await db.update("profiles", {"account_status": "deactivated"}, query={"clerk_user_id": f"eq.{user_id}"})
    finally:
        await db.aclose()
    return {"received": True}
