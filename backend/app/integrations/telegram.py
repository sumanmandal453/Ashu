from __future__ import annotations

import httpx

from app.core.config import settings
from app.core.exceptions import ExternalServiceError


class TelegramClient:
    async def send_message(self, chat_id: str, text: str) -> dict:
        if not settings.telegram_bot_token:
            raise ExternalServiceError("Telegram bot token is not configured")
        url = f"https://api.telegram.org/bot{settings.telegram_bot_token}/sendMessage"
        async with httpx.AsyncClient(timeout=20) as client:
            response = await client.post(url, json={"chat_id": chat_id, "text": text, "disable_web_page_preview": True})
            response.raise_for_status()
            payload = response.json()
            if not payload.get("ok"):
                raise ExternalServiceError("Telegram did not accept the message")
            return payload.get("result", {})

    async def send_document(self, chat_id: str, filename: str, data: bytes, caption: str = "") -> dict:
        if not settings.telegram_bot_token:
            raise ExternalServiceError("Telegram bot token is not configured")
        url = f"https://api.telegram.org/bot{settings.telegram_bot_token}/sendDocument"
        files = {"document": (filename, data)}
        async with httpx.AsyncClient(timeout=60) as client:
            response = await client.post(url, data={"chat_id": chat_id, "caption": caption}, files=files)
            response.raise_for_status()
            payload = response.json()
            if not payload.get("ok"):
                raise ExternalServiceError("Telegram did not accept the document")
            return payload.get("result", {})
