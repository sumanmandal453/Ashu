from __future__ import annotations

from app.core.config import settings
from app.core.exceptions import ExternalServiceError


class GroqProvider:
    def __init__(self):
        if not settings.groq_api_key:
            raise ExternalServiceError("Groq API key is not configured")
        try:
            from groq import AsyncGroq
        except ImportError as exc:
            raise ExternalServiceError("Install groq to use Groq") from exc
        self.client = AsyncGroq(api_key=settings.groq_api_key)

    async def generate_text(self, prompt: str) -> str:
        try:
            response = await self.client.chat.completions.create(
                model=settings.groq_model,
                messages=[{"role": "user", "content": prompt}],
                temperature=0.3,
            )
            return response.choices[0].message.content or ""
        except Exception as exc:
            raise ExternalServiceError("Groq request failed") from exc
