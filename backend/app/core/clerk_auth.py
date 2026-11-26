from dataclasses import dataclass
from typing import Any

from fastapi import Depends, HTTPException, Request, status

from app.core.config import settings


@dataclass(frozen=True)
class CurrentUser:
    user_id: str
    claims: dict[str, Any]


def verify_clerk_request(request: Request) -> CurrentUser:
    """Verify the existing Clerk session. This does not start a second login flow."""
    if not settings.clerk_secret_key:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Clerk backend verification is not configured",
        )
    try:
        from clerk_backend_api import AuthenticateRequestOptions, authenticate_request

        state = authenticate_request(
            request,
            AuthenticateRequestOptions(
                secret_key=settings.clerk_secret_key,
                jwt_key=settings.clerk_jwt_key,
                authorized_parties=settings.clerk_party_list or None,
                accepts_token=["session_token"],
            ),
        )
    except ImportError as exc:
        raise HTTPException(503, "Install the clerk-backend-api package") from exc
    except Exception as exc:
        # Avoid returning SDK internals or token contents to clients.
        raise HTTPException(status_code=401, detail="Invalid or expired Clerk session") from exc

    if not getattr(state, "is_signed_in", False):
        reason = getattr(state, "reason", None)
        detail = getattr(reason, "name", None) or "Authentication required"
        raise HTTPException(status_code=401, detail=detail)

    payload = getattr(state, "payload", None) or {}
    if hasattr(payload, "model_dump"):
        payload = payload.model_dump()
    elif not isinstance(payload, dict):
        try:
            payload = dict(payload)
        except Exception:
            payload = {}
    user_id = payload.get("sub")
    if not isinstance(user_id, str) or not user_id.startswith("user_"):
        raise HTTPException(status_code=401, detail="Clerk token has no valid user subject")
    return CurrentUser(user_id=user_id, claims=payload)


async def get_current_user(request: Request) -> CurrentUser:
    return verify_clerk_request(request)


async def require_authenticated_user(user: CurrentUser = Depends(get_current_user)) -> CurrentUser:
    return user
