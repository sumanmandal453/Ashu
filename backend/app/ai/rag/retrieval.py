from app.database.supabase_rest import SupabaseRestClient
from app.ai.rag.embeddings import embed_texts


async def search_material_chunks(db: SupabaseRestClient, user_id: str, query_text: str, *, limit: int = 5) -> list[dict]:
    vectors = await embed_texts([query_text], task_type="RETRIEVAL_QUERY")
    result = await db.rpc("match_material_chunks", {
        "query_embedding": vectors[0],
        "match_count": limit,
        "filter_user_id": user_id,
    })
    return result or []
