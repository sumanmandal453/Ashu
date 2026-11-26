from __future__ import annotations

import json
from typing import Any

from app.core.config import settings
from app.core.exceptions import ExternalServiceError


class GeminiProvider:
    def __init__(self):
        if not settings.gemini_api_key:
            raise ExternalServiceError("Gemini API key is not configured")
        try:
            from google import genai
        except ImportError as exc:
            raise ExternalServiceError("Install google-genai to use Gemini") from exc
        self.client = genai.Client(api_key=settings.gemini_api_key)
        self.model = settings.gemini_model

    async def generate_text(self, prompt: str, *, json_mode: bool = False) -> str:
        try:
            from google.genai import types
            config = types.GenerateContentConfig(
                temperature=0.3,
                response_mime_type="application/json" if json_mode else None,
            )
            response = await self.client.aio.models.generate_content(
                model=self.model, contents=prompt, config=config
            )
            return response.text or ""
        except Exception as exc:
            raise ExternalServiceError("Gemini request failed") from exc

    async def generate_json(self, prompt: str) -> dict[str, Any]:
        text = await self.generate_text(prompt, json_mode=True)
        try:
            value = json.loads(text)
            if not isinstance(value, dict):
                raise ValueError("Expected JSON object")
            return value
        except (json.JSONDecodeError, ValueError) as exc:
            raise ExternalServiceError("Gemini returned invalid structured output") from exc
