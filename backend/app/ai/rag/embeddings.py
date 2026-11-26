from app.core.config import settings
from app.core.exceptions import ExternalServiceError


async def embed_texts(texts: list[str], task_type: str = "RETRIEVAL_DOCUMENT") -> list[list[float]]:
    if not settings.gemini_api_key:
        raise ExternalServiceError("Gemini API key is not configured for embeddings")
    try:
        from google import genai
        from google.genai import types
        client = genai.Client(api_key=settings.gemini_api_key)
        result = []
        for text in texts:
            response = await client.aio.models.embed_content(
                model="gemini-embedding-001",
                contents=text,
                config=types.EmbedContentConfig(
                    task_type=task_type,
                    output_dimensionality=768,
                ),
            )
            values = response.embeddings[0].values
            if len(values) != 768:
                raise ValueError(f"Expected 768 embedding dimensions, received {len(values)}")
            result.append(list(values))
        return result
    except Exception as exc:
        raise ExternalServiceError("Embedding generation failed; verify model and API access") from exc
