from fastapi import APIRouter, Depends, File, HTTPException, UploadFile
from app.core.clerk_auth import CurrentUser, get_current_user
from app.core.config import settings
from app.core.dependencies import get_supabase
from app.core.responses import success
from app.database.supabase_rest import SupabaseRestClient
from app.utils.file_validation import validate_upload
from app.utils.hashing import sha256_bytes
from app.services.queue_service import enqueue_job

router = APIRouter(prefix="/materials", tags=["study materials"])


@router.post("/upload")
async def upload_material(file: UploadFile = File(...), subject_id: str | None = None,
                         user: CurrentUser = Depends(get_current_user), db: SupabaseRestClient = Depends(get_supabase)):
    data = await file.read(settings.max_upload_bytes + 1)
    try:
        validate_upload(file.filename or "upload", file.content_type or "application/octet-stream", len(data), settings.max_upload_bytes)
    except ValueError as exc:
        raise HTTPException(415 if "Unsupported" in str(exc) else 413, str(exc)) from exc
    checksum = sha256_bytes(data)
    file_id_path = f"{user.user_id}/{checksum}/{file.filename}"
    await db.upload("study-materials", file_id_path, data, file.content_type or "application/octet-stream")
    rows = await db.insert("study_materials", {
        "user_id": user.user_id, "subject_id": subject_id, "file_name": file.filename,
        "storage_path": file_id_path, "file_type": file.content_type, "file_size": len(data),
        "content_hash": checksum, "processing_status": "queued",
    })
    material = rows[0] if rows else {}
    await enqueue_job("assignment-processing", {"task_type": "material.ingest", "user_id": user.user_id, "material_id": material.get("id")})
    return success(material, "Study material uploaded and queued for processing")


@router.get("")
async def list_materials(user: CurrentUser = Depends(get_current_user), db: SupabaseRestClient = Depends(get_supabase)):
    rows = await db.select("study_materials", query={"user_id": f"eq.{user.user_id}"}, order="uploaded_at.desc", limit=200)
    return success(rows)


@router.get("/{material_id}")
async def get_material(material_id: str, user: CurrentUser = Depends(get_current_user), db: SupabaseRestClient = Depends(get_supabase)):
    rows = await db.select("study_materials", query={"id": f"eq.{material_id}", "user_id": f"eq.{user.user_id}"}, limit=1)
    if not rows:
        raise HTTPException(404, "Material not found")
    row = rows[0]
    row["download_url"] = await db.signed_url("study-materials", row["storage_path"])
    return success(row)


@router.post("/{material_id}/process")
async def process_material(material_id: str, user: CurrentUser = Depends(get_current_user), db: SupabaseRestClient = Depends(get_supabase)):
    rows = await db.select("study_materials", query={"id": f"eq.{material_id}", "user_id": f"eq.{user.user_id}"}, limit=1)
    if not rows:
        raise HTTPException(404, "Material not found")
    await enqueue_job("assignment-processing", {"task_type": "material.ingest", "user_id": user.user_id, "material_id": material_id})
    return success({"queued": True})


@router.delete("/{material_id}")
async def delete_material(material_id: str, user: CurrentUser = Depends(get_current_user), db: SupabaseRestClient = Depends(get_supabase)):
    rows = await db.select("study_materials", query={"id": f"eq.{material_id}", "user_id": f"eq.{user.user_id}"}, limit=1)
    if not rows:
        raise HTTPException(404, "Material not found")
    await db.delete("study_materials", query={"id": f"eq.{material_id}", "user_id": f"eq.{user.user_id}"})
    return success({"deleted": True})
