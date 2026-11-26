from fastapi import APIRouter, Depends, HTTPException
from app.core.clerk_auth import CurrentUser, get_current_user
from app.core.dependencies import get_supabase
from app.core.responses import success
from app.database.supabase_rest import SupabaseRestClient
from app.schemas.assignment import GenerateAnswerRequest, SummaryRequest
from app.services.ai_service import AIService

router = APIRouter(prefix="/ai", tags=["ai"])


@router.post("/generate-summary")
async def generate_summary(payload: SummaryRequest, user: CurrentUser = Depends(get_current_user), db: SupabaseRestClient = Depends(get_supabase)):
    assignments = await db.select("assignments", query={"id": f"eq.{payload.assignment_id}", "user_id": f"eq.{user.user_id}"}, limit=1)
    if not assignments:
        raise HTTPException(404, "Assignment not found")
    result = await AIService().summarize_assignment(assignments[0])
    inserted = await db.insert("assignment_summaries", {"user_id": user.user_id, "assignment_id": payload.assignment_id, **result})
    return success(inserted[0] if inserted else result, "Assignment summary generated")


@router.post("/generate-answer")
async def generate_answer(payload: GenerateAnswerRequest, user: CurrentUser = Depends(get_current_user), db: SupabaseRestClient = Depends(get_supabase)):
    if payload.assignment_id:
        owned = await db.select("assignments", query={"id": f"eq.{payload.assignment_id}", "user_id": f"eq.{user.user_id}"}, limit=1)
        if not owned:
            raise HTTPException(404, "Assignment not found")
    references = []
    try:
        from app.ai.rag.retrieval import search_material_chunks
        hits = await search_material_chunks(db, user.user_id, payload.question, limit=5)
        references = [str(hit.get("chunk_text", "")) for hit in hits if hit.get("chunk_text")]
    except Exception:
        # RAG is optional; a missing embedding key or empty knowledge base must not
        # prevent ordinary answer drafting. The failure is intentionally not exposed.
        references = []
    answer = await AIService().generate_answer(
        question=payload.question, subject=payload.subject, marks=payload.marks,
        length=payload.answer_length, language=payload.language, style=payload.style,
        references=references,
    )
    source_references = [{"material_id": hit.get("material_id"), "page_number": hit.get("page_number"), "similarity": hit.get("similarity")} for hit in hits if hit.get("material_id")] if references else []
    row = {"user_id": user.user_id, "assignment_id": payload.assignment_id, "question_text": payload.question, "answer_text": answer,
           "ai_provider": "gemini", "generation_status": "draft", "source_references": source_references}
    inserted = await db.insert("generated_answers", row)
    return success({"answer": answer, "record": inserted[0] if inserted else None}, "Answer draft generated")


@router.post("/improve-answer")
async def improve_answer(payload: dict, user: CurrentUser = Depends(get_current_user)):
    answer = str(payload.get("answer", ""))
    instruction = str(payload.get("instruction", "Improve clarity, structure and correctness"))
    if not answer.strip():
        raise HTTPException(422, "answer is required")
    improved = await AIService().generate_text(f"Improve this academic answer according to: {instruction}. Do not invent references.\n\n{answer}")
    return success({"answer": improved})


@router.post("/check-completeness")
async def check_completeness(payload: dict, user: CurrentUser = Depends(get_current_user)):
    question = str(payload.get("question", "")); answer = str(payload.get("answer", ""))
    if not question or not answer:
        raise HTTPException(422, "question and answer are required")
    result = await AIService().generate_json(
        "Return JSON with keys completeness_score (0-100), missing_points (array), suggestions (array), "
        "and disclaimer. Evaluate the answer against the question without claiming certainty.\n"
        f"QUESTION: {question}\nANSWER: {answer}"
    )
    return success(result)
