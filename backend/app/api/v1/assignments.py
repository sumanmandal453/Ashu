from fastapi import APIRouter, Depends, File, HTTPException, Query, UploadFile
from app.core.clerk_auth import CurrentUser, get_current_user
from app.core.dependencies import get_supabase
from app.core.responses import paginated, success
from app.database.repositories import Repository
from app.database.supabase_rest import SupabaseRestClient
from app.schemas.assignment import AssignmentCreate, AssignmentUpdate
from app.services.assignment_service import AssignmentService
from app.services.queue_service import enqueue_job
from app.core.config import settings
from app.utils.file_validation import validate_upload
from app.utils.hashing import sha256_bytes

router = APIRouter(prefix="/assignments", tags=["assignments"])


@router.get("")
async def list_assignments(
    status: str | None = None,
    subject_id: str | None = None,
    search: str | None = None,
    sort_by: str = "deadline",
    sort_order: str = "asc",
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    user: CurrentUser = Depends(get_current_user), db: SupabaseRestClient = Depends(get_supabase),
):
    service = AssignmentService(Repository(db, user.user_id))
    rows, total = await service.list_assignments(status, subject_id, search, sort_by, sort_order, page, page_size)
    return paginated(rows, page, page_size, total)


@router.post("")
async def create_manual_assignment(payload: AssignmentCreate, user: CurrentUser = Depends(get_current_user), db: SupabaseRestClient = Depends(get_supabase)):
    values = payload.model_dump(mode="json")
    if values.get("subject_id"):
        subject = await db.select("subjects", query={"id": f"eq.{values['subject_id']}", "user_id": f"eq.{user.user_id}"}, limit=1)
        if not subject:
            raise HTTPException(404, "Subject not found")
    row = await db.insert("assignments", {"user_id": user.user_id, **values, "workflow_status": "new", "source_platform": "manual"})
    return success(row[0] if row else {}, "Assignment created")


@router.get("/{assignment_id}")
async def get_assignment(assignment_id: str, user: CurrentUser = Depends(get_current_user), db: SupabaseRestClient = Depends(get_supabase)):
    repo = Repository(db, user.user_id)
    row = await repo.get_owned("assignments", assignment_id)
    if not row:
        raise HTTPException(404, "Assignment not found")
    return success(row)


@router.patch("/{assignment_id}")
async def update_assignment(assignment_id: str, payload: AssignmentUpdate, user: CurrentUser = Depends(get_current_user), db: SupabaseRestClient = Depends(get_supabase)):
    values = payload.model_dump(exclude_unset=True, mode="json")
    row = await Repository(db, user.user_id).update_owned("assignments", assignment_id, values)
    if not row:
        raise HTTPException(404, "Assignment not found")
    return success(row, "Assignment updated")


@router.get("/{assignment_id}/summary")
async def get_summary(assignment_id: str, user: CurrentUser = Depends(get_current_user), db: SupabaseRestClient = Depends(get_supabase)):
    await _owned_assignment(db, user.user_id, assignment_id)
    rows = await db.select("assignment_summaries", query={"user_id": f"eq.{user.user_id}", "assignment_id": f"eq.{assignment_id}"}, order="generated_at.desc", limit=1)
    return success(rows[0] if rows else None)


@router.get("/{assignment_id}/attachments")
async def get_attachments(assignment_id: str, user: CurrentUser = Depends(get_current_user), db: SupabaseRestClient = Depends(get_supabase)):
    await _owned_assignment(db, user.user_id, assignment_id)
    rows = await db.select("assignment_attachments", query={"user_id": f"eq.{user.user_id}", "assignment_id": f"eq.{assignment_id}"}, limit=100)
    return success(rows)


@router.post("/{assignment_id}/process")
async def process_assignment(assignment_id: str, user: CurrentUser = Depends(get_current_user), db: SupabaseRestClient = Depends(get_supabase)):
    await _owned_assignment(db, user.user_id, assignment_id)
    job = {"task_type": "assignment.process", "user_id": user.user_id, "assignment_id": assignment_id}
    await enqueue_job("assignment-processing", job)
    return success({"queued": True}, "Assignment processing queued")


@router.post("/{assignment_id}/attachments/upload")
async def upload_assignment_attachment(assignment_id: str, file: UploadFile = File(...), user: CurrentUser = Depends(get_current_user), db: SupabaseRestClient = Depends(get_supabase)):
    assignment = await _owned_assignment(db, user.user_id, assignment_id)
    data = await file.read(settings.max_upload_bytes + 1)
    try:
        validate_upload(file.filename or "attachment", file.content_type or "application/octet-stream", len(data), settings.max_upload_bytes)
    except ValueError as exc:
        raise HTTPException(415, str(exc)) from exc
    checksum = sha256_bytes(data)
    path = f"{user.user_id}/{assignment_id}/{checksum}/{file.filename}"
    await db.upload("assignment-files", path, data, file.content_type or "application/octet-stream")
    rows = await db.insert("assignment_attachments", {
        "user_id": user.user_id, "assignment_id": assignment_id, "original_file_name": file.filename or "attachment",
        "storage_path": path, "file_type": file.content_type, "file_size": len(data), "content_hash": checksum,
        "extraction_status": "pending",
    })
    await enqueue_job("assignment-processing", {"task_type": "assignment.process", "user_id": user.user_id, "assignment_id": assignment_id})
    return success(rows[0] if rows else {}, "Attachment uploaded and assignment analysis queued")


async def _owned_assignment(db: SupabaseRestClient, user_id: str, assignment_id: str):
    rows = await db.select("assignments", query={"id": f"eq.{assignment_id}", "user_id": f"eq.{user_id}"}, limit=1)
    if not rows:
        raise HTTPException(404, "Assignment not found")
    return rows[0]
