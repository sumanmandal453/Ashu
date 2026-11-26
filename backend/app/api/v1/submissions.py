from fastapi import APIRouter, Depends, HTTPException
from app.core.clerk_auth import CurrentUser, get_current_user
from app.core.dependencies import get_supabase
from app.core.exceptions import IntegrationUnavailable
from app.core.responses import success
from app.database.supabase_rest import SupabaseRestClient
from app.services.submission_service import DigiicampusSubmissionProvider

router = APIRouter(prefix="/submissions", tags=["submissions"])


@router.get("")
async def list_submissions(user: CurrentUser = Depends(get_current_user), db: SupabaseRestClient = Depends(get_supabase)):
    rows = await db.select("submission_attempts", query={"user_id": f"eq.{user.user_id}"}, order="created_at.desc", limit=200)
    return success(rows)


@router.get("/history")
async def history(user: CurrentUser = Depends(get_current_user), db: SupabaseRestClient = Depends(get_supabase)):
    return await list_submissions(user, db)


@router.post("/{submission_id}/approve")
async def approve(submission_id: str, user: CurrentUser = Depends(get_current_user), db: SupabaseRestClient = Depends(get_supabase)):
    rows = await db.select("submission_attempts", query={"id": f"eq.{submission_id}", "user_id": f"eq.{user.user_id}"}, limit=1)
    if not rows:
        raise HTTPException(404, "Submission record not found")
    submission = rows[0]
    docs = await db.select("generated_documents", query={"id": f"eq.{submission['document_id']}", "user_id": f"eq.{user.user_id}"}, limit=1)
    if not docs:
        raise HTTPException(404, "Document not found")
    doc = docs[0]
    if doc.get("approval_status") == "approved":
        return success({"approved": True}, "Document already approved")
    approvals = await db.insert("approval_records", {
        "user_id": user.user_id, "assignment_id": submission["assignment_id"],
        "document_id": doc["id"], "document_checksum": doc["checksum"], "approval_status": "approved",
    })
    await db.update("generated_documents", {"approval_status": "approved"}, query={"id": f"eq.{doc['id']}", "user_id": f"eq.{user.user_id}"})
    await db.update("assignments", {"workflow_status": "in_progress"}, query={"id": f"eq.{submission['assignment_id']}", "user_id": f"eq.{user.user_id}"})
    await db.update("submission_attempts", {"approval_status": "approved", "approval_record_id": approvals[0]["id"] if approvals else None}, query={"id": f"eq.{submission_id}", "user_id": f"eq.{user.user_id}"})
    return success({"approved": True, "approval": approvals[0] if approvals else None}, "Document approved")


@router.post("/{submission_id}/attempt")
async def attempt(submission_id: str, user: CurrentUser = Depends(get_current_user), db: SupabaseRestClient = Depends(get_supabase)):
    rows = await db.select("submission_attempts", query={"id": f"eq.{submission_id}", "user_id": f"eq.{user.user_id}"}, limit=1)
    if not rows:
        raise HTTPException(404, "Submission record not found")
    submission = rows[0]
    if submission.get("approval_status") != "approved":
        raise HTTPException(409, "Explicit approval is required before submission")
    docs = await db.select("generated_documents", query={"id": f"eq.{submission['document_id']}", "user_id": f"eq.{user.user_id}"}, limit=1)
    if not docs:
        raise HTTPException(404, "Approved document not found")
    approval_id = submission.get("approval_record_id")
    approvals = await db.select("approval_records", query={"id": f"eq.{approval_id}", "user_id": f"eq.{user.user_id}", "document_id": f"eq.{docs[0]['id']}", "approval_status": "eq.approved", "revoked_at": "is.null"}, limit=1) if approval_id else []
    if not approvals or approvals[0].get("document_checksum") != docs[0].get("checksum"):
        raise HTTPException(409, "A valid approval for this exact document version is required")
    try:
        await DigiicampusSubmissionProvider().submit_assignment(submission=submission, document=docs[0])
    except IntegrationUnavailable as exc:
        await db.update("submission_attempts", {"submission_status": "manual_submission_required", "failure_reason": str(exc)}, query={"id": f"eq.{submission_id}", "user_id": f"eq.{user.user_id}"})
        return success({"submission_status": "manual_submission_required", "reason": str(exc)}, "Automatic submission is not enabled; submit the approved file manually")


@router.get("/{submission_id}/status")
async def status(submission_id: str, user: CurrentUser = Depends(get_current_user), db: SupabaseRestClient = Depends(get_supabase)):
    rows = await db.select("submission_attempts", query={"id": f"eq.{submission_id}", "user_id": f"eq.{user.user_id}"}, limit=1)
    if not rows:
        raise HTTPException(404, "Submission record not found")
    return success(rows[0])
