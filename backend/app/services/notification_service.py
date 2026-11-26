from __future__ import annotations

from app.integrations.telegram import TelegramClient
from app.integrations.whatsapp import WhatsAppClient


class NotificationService:
    async def send_telegram(self, chat_id: str, title: str, message: str) -> dict:
        return await TelegramClient().send_message(chat_id, f"{title}\n\n{message}")

    async def send_whatsapp_template(self, phone: str, template: str, language: str = "en_US") -> dict:
        return await WhatsAppClient().send_template(phone, template, language)
