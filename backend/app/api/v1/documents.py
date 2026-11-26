from fastapi import APIRouter, Depends, File, HTTPException, UploadFile
from app.core.clerk_auth import CurrentUser, get_current_user
from app.core.dependencies import get_supabase
from app.core.responses import success
from app.database.supabase_rest import SupabaseRestClient
from app.documents.generate import generate_docx, generate_pdf
from app.schemas.documents import DocumentGenerateRequest
from app.utils.hashing import sha256_bytes
from app.core.config import settings
from app.utils.file_validation import validate_upload

router = APIRouter(prefix="/documents", tags=["documents"])


@router.post("/generate")
async def generate_document(payload: DocumentGenerateRequest, user: CurrentUser = Depends(get_current_user), db: SupabaseRestClient = Depends(get_supabase)):
    assignment_rows = await db.select("assignments", query={"id": f"eq.{payload.assignment_id}", "user_id": f"eq.{user.user_id}"}, limit=1)
    if not assignment_rows:
        raise HTTPException(404, "Assignment not found")
    assignment = assignment_rows[0]
    answers = await db.select("generated_answers", query={"assignment_id": f"eq.{payload.assignment_id}", "user_id": f"eq.{user.user_id}"}, order="created_at.asc", limit=100)
    qa = [{"question": str(a.get("question_text") or "Question"), "answer": a.get("answer_text", "")} for a in answers]
    if not qa:
        questions = await db.select("assignment_questions", query={"assignment_id": f"eq.{payload.assignment_id}", "user_id": f"eq.{user.user_id}"}, order="question_number.asc", limit=100)
        qa = [{"question": q.get("question_text", ""), "answer": ""} for q in questions]
    if not qa or not any(item.get("answer", "").strip() for item in qa):
        raise HTTPException(409, "Generate or save at least one answer before creating the final document")
    profile_rows = await db.select("profiles", query={"clerk_user_id": f"eq.{user.user_id}"}, limit=1)
    profile = profile_rows[0] if profile_rows else {}
    subject = assignment.get("subject_name") or ""
    if payload.format == "docx":
        data = generate_docx(assignment["title"], profile, subject, qa)
        content_type = "application/vnd.openxmlformats-officedocument.wordprocessingml.document"
        ext = "docx"
    else:
        data = generate_pdf(assignment["title"], profile, subject, qa)
        content_type = "application/pdf"
        ext = "pdf"
    checksum = sha256_bytes(data)
    instructions_text = " ".join(str(x or "") for x in [assignment.get("description"), assignment.get("instructions")]).lower()
    requires_handwriting = any(term in instructions_text for term in ["handwritten", "hand written", "hand-written", "scanned copy", "write by hand"])
    filename = f"{assignment['title'][:70]}.{ext}"
    path = f"{user.user_id}/{payload.assignment_id}/{checksum}.{ext}"
    await db.upload("generated-documents", path, data, content_type)
    existing = await db.select("generated_documents", query={"user_id": f"eq.{user.user_id}", "assignment_id": f"eq.{payload.assignment_id}"}, order="version_number.desc", limit=1)
    version = (int(existing[0].get("version_number", 0)) + 1) if existing else 1
    rows = await db.insert("generated_documents", {
        "user_id": user.user_id, "assignment_id": payload.assignment_id, "file_name": filename,
        "file_format": ext, "storage_path": path, "version_number": version,
        "checksum": checksum, "approval_status": "awaiting_review", "requires_handwritten_submission": requires_handwriting,
    })
    document = rows[0] if rows else {}
    if document.get("id"):
        await db.update("assignments", {"workflow_status": "awaiting_approval"}, query={"id": f"eq.{payload.assignment_id}", "user_id": f"eq.{user.user_id}"})
        await db.insert("submission_attempts", {
            "user_id": user.user_id, "assignment_id": payload.assignment_id, "document_id": document["id"],
            "approval_status": "awaiting_approval", "submission_status": "not_started",
        })
    warning = "This assignment appears to require handwritten and scanned work. This generated file is a printable draft, not a final submission." if requires_handwriting else None
    return success({"document": document, "download_url": await db.signed_url("generated-documents", path), "warning": warning}, "Document generated")


@router.post("/{document_id}/upload-handwritten-scan")
async def upload_handwritten_scan(document_id: str, file: UploadFile = File(...), user: CurrentUser = Depends(get_current_user), db: SupabaseRestClient = Depends(get_supabase)):
    original = await db.select("generated_documents", query={"id": f"eq.{document_id}", "user_id": f"eq.{user.user_id}"}, limit=1)
    if not original:
        raise HTTPException(404, "Original document not found")
    if not original[0].get("requires_handwritten_submission"):
        raise HTTPException(409, "This assignment is not marked as requiring a handwritten scan")
    if (file.filename or "").lower().endswith(".pdf") is False or file.content_type != "application/pdf":
        raise HTTPException(415, "Upload the scanned handwritten work as a PDF")
    data = await file.read(settings.max_upload_bytes + 1)
    try:
        validate_upload(file.filename or "scan.pdf", file.content_type, len(data), settings.max_upload_bytes)
    except ValueError as exc:
        raise HTTPException(413, str(exc)) from exc
    checksum = sha256_bytes(data)
    assignment_id = original[0]["assignment_id"]
    path = f"{user.user_id}/{assignment_id}/{checksum}.pdf"
    await db.upload("generated-documents", path, data, "application/pdf")
    versions = await db.select("generated_documents", query={"user_id": f"eq.{user.user_id}", "assignment_id": f"eq.{assignment_id}"}, order="version_number.desc", limit=1)
    version = int(versions[0].get("version_number", 0)) + 1 if versions else 1
    created = await db.insert("generated_documents", {
        "user_id": user.user_id, "assignment_id": assignment_id, "file_name": file.filename or "handwritten-scan.pdf",
        "file_format": "pdf", "storage_path": path, "version_number": version, "checksum": checksum,
        "approval_status": "awaiting_review", "requires_handwritten_submission": False,
    })
    new_doc = created[0] if created else {}
    if new_doc.get("id"):
        await db.insert("submission_attempts", {
            "user_id": user.user_id, "assignment_id": assignment_id, "document_id": new_doc["id"],
            "approval_status": "awaiting_approval", "submission_status": "not_started",
        })
    return success({"document": new_doc, "download_url": await db.signed_url("generated-documents", path)}, "Scanned PDF uploaded for review")


@router.get("")
async def list_documents(user: CurrentUser = Depends(get_current_user), db: SupabaseRestClient = Depends(get_supabase)):
    rows = await db.select("generated_documents", query={"user_id": f"eq.{user.user_id}"}, order="generated_at.desc", limit=200)
    return success(rows)


@router.get("/{document_id}")
async def get_document(document_id: str, user: CurrentUser = Depends(get_current_user), db: SupabaseRestClient = Depends(get_supabase)):
    rows = await db.select("generated_documents", query={"id": f"eq.{document_id}", "user_id": f"eq.{user.user_id}"}, limit=1)
    if not rows:
        raise HTTPException(404, "Document not found")
    row = rows[0]
    row["download_url"] = await db.signed_url("generated-documents", row["storage_path"])
    return success(row)


@router.get("/{document_id}/download")
async def download_document(document_id: str, user: CurrentUser = Depends(get_current_user), db: SupabaseRestClient = Depends(get_supabase)):
    return await get_document(document_id, user, db)


@router.delete("/{document_id}")
async def delete_document(document_id: str, user: CurrentUser = Depends(get_current_user), db: SupabaseRestClient = Depends(get_supabase)):
    rows = await db.select("generated_documents", query={"id": f"eq.{document_id}", "user_id": f"eq.{user.user_id}"}, limit=1)
    if not rows:
        raise HTTPException(404, "Document not found")
    await db.delete("generated_documents", query={"id": f"eq.{document_id}", "user_id": f"eq.{user.user_id}"})
    return success({"deleted": True})
