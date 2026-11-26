from __future__ import annotations

import httpx

from app.core.config import settings
from app.core.exceptions import ExternalServiceError


class WhatsAppClient:
    async def send_template(self, to: str, template_name: str, language: str = "en_US", components: list[dict] | None = None) -> dict:
        if not settings.whatsapp_access_token or not settings.whatsapp_phone_number_id:
            raise ExternalServiceError("WhatsApp Business Platform is not configured")
        url = f"https://graph.facebook.com/{settings.whatsapp_api_version}/{settings.whatsapp_phone_number_id}/messages"
        payload = {
            "messaging_product": "whatsapp", "to": to, "type": "template",
            "template": {"name": template_name, "language": {"code": language}, "components": components or []},
        }
        headers = {"Authorization": f"Bearer {settings.whatsapp_access_token}", "Content-Type": "application/json"}
        async with httpx.AsyncClient(timeout=30) as client:
            response = await client.post(url, json=payload, headers=headers)
            response.raise_for_status()
            return response.json()
