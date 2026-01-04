from fastapi import APIRouter, Depends, UploadFile, File, HTTPException
from sqlalchemy.orm import Session
from app.database import get_db
from app.dependencies import get_current_user
import os
from app.config import (
    UPLOAD_DIR,
    CLOUDINARY_ENABLED,
    CLOUDINARY_URL,
    CLOUDINARY_CLOUD_NAME,
    CLOUDINARY_API_KEY,
    CLOUDINARY_API_SECRET,
)
from uuid import uuid4
from app import models
from app.crud.crud import create_document, list_documents_for_trip, get_document, delete_document
from app.schemas.response import ApiResponse  # Thêm dòng này
import io

router = APIRouter(prefix="/documents", tags=["documents"])

os.makedirs(UPLOAD_DIR, exist_ok=True)
_AVATAR_CATEGORIES = {"avatar", "user_avatar"}
_TRIP_COVER_CATEGORIES = {"cover", "trip_cover", "cover_image"}

@router.post("/upload", response_model=ApiResponse)
async def upload(
    trip_id: int | None = None,
    category: str | None = None,
    file: UploadFile = File(...),
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user),
):
    # Validate file size (max 10MB)
    MAX_FILE_SIZE = 10 * 1024 * 1024  # 10MB
    content = await file.read()
    if len(content) > MAX_FILE_SIZE:
        raise HTTPException(400, "File quá lớn. Kích thước tối đa là 10MB")
    normalized_category = (category or "").strip().lower() or None
    # Validate file type
    if normalized_category in _AVATAR_CATEGORIES or normalized_category in _TRIP_COVER_CATEGORIES:
        allowed_extensions = {".jpg", ".jpeg", ".png", ".webp"}
    else:
        allowed_extensions = {".pdf", ".jpg", ".jpeg", ".png", ".doc", ".docx", ".txt"}

    ext = os.path.splitext(file.filename or "")[1].lower()
    if ext not in allowed_extensions:
        raise HTTPException(
            400,
            f"Định dạng file không được hỗ trợ. Chỉ cho phép: {', '.join(sorted(allowed_extensions))}",
        )

    if trip_id is None and normalized_category not in _AVATAR_CATEGORIES:
        raise HTTPException(400, "Thiếu trip_id")
    
    # Save file (Render free filesystem is ephemeral; prefer Cloudinary)
    url: str
    if CLOUDINARY_ENABLED:
        try:
            import cloudinary
            import cloudinary.uploader

            if CLOUDINARY_URL:
                cloudinary.config(cloudinary_url=CLOUDINARY_URL, secure=True)
            else:
                cloudinary.config(
                    cloud_name=CLOUDINARY_CLOUD_NAME,
                    api_key=CLOUDINARY_API_KEY,
                    api_secret=CLOUDINARY_API_SECRET,
                    secure=True,
                )

            # Route uploads by intent so avatar/cover don't end up as trip documents.
            if normalized_category in _AVATAR_CATEGORIES:
                folder = f"tripsync/avatars/user_{current_user.id}"
                resource_type = "image"
                overwrite = True
            elif normalized_category in _TRIP_COVER_CATEGORIES:
                folder = f"tripsync/trips/trip_{trip_id}/cover"
                resource_type = "image"
                overwrite = True
            else:
                folder = "tripsync"
                if trip_id:
                    folder = f"{folder}/trip_{trip_id}"
                if normalized_category:
                    folder = f"{folder}/{normalized_category}"
                resource_type = "auto"
                overwrite = False

            public_id = uuid4().hex
            upload_result = cloudinary.uploader.upload(
                io.BytesIO(content),
                resource_type=resource_type,
                folder=folder,
                public_id=public_id,
                overwrite=overwrite,
            )

            secure_url = upload_result.get("secure_url")
            if not secure_url:
                raise RuntimeError("Cloudinary upload did not return secure_url")
            url = str(secure_url)
        except Exception as e:
            raise HTTPException(500, f"Upload Cloudinary thất bại: {e}")
    else:
        if normalized_category in _AVATAR_CATEGORIES:
            name = f"avatar_{current_user.id}_{uuid4().hex}{ext}"
        elif normalized_category in _TRIP_COVER_CATEGORIES:
            name = f"trip_{trip_id}_cover_{uuid4().hex}{ext}"
        else:
            name = f"{uuid4().hex}{ext}"
        path = os.path.join(UPLOAD_DIR, name)
        with open(path, "wb") as f:
            f.write(content)

        url = f"/uploads/{name}"

    # Persist depending on category
    if normalized_category in _AVATAR_CATEGORIES:
        from app.crud.crud import update_user_profile

        updated_user = update_user_profile(db, current_user.id, current_user.name, url)
        if not updated_user:
            raise HTTPException(404, "Người dùng không tồn tại")
        return ApiResponse(message="Tải avatar thành công", data={"url": url})

    if normalized_category in _TRIP_COVER_CATEGORIES:
        from app.crud.crud import get_trip

        trip = get_trip(db, trip_id)
        if not trip:
            raise HTTPException(404, "Chuyến đi không tồn tại")
        if trip.owner_id != current_user.id:
            raise HTTPException(403, "Chỉ chủ nhóm mới có thể cập nhật ảnh bìa")

        trip.cover_image_url = url
        db.commit()
        db.refresh(trip)
        return ApiResponse(message="Cập nhật ảnh bìa thành công", data={"url": url})

    doc = create_document(
        db,
        trip_id=trip_id,
        uploader_id=current_user.id,
        filename=file.filename or "",
        url=url,
        category=normalized_category,
    )
    return ApiResponse(message="Tải lên thành công", data=doc)

@router.get("/trip/{trip_id}", response_model=ApiResponse)
def list_docs(trip_id: int, db: Session = Depends(get_db), current_user = Depends(get_current_user)):
    docs = list_documents_for_trip(db, trip_id)
    return ApiResponse(message="Danh sách tài liệu", data=docs)


@router.get("/{document_id}", response_model=ApiResponse)
def get_document_endpoint(document_id: int, db: Session = Depends(get_db), current_user = Depends(get_current_user)):
    doc = get_document(db, document_id)
    if not doc:
        raise HTTPException(status_code=404, detail="Tài liệu không tồn tại")

    is_member = db.query(models.trip.TripMember).filter(
        models.trip.TripMember.trip_id == doc.trip_id,
        models.trip.TripMember.user_id == current_user.id,
    ).first()
    if not is_member:
        raise HTTPException(status_code=403, detail="Không có quyền truy cập tài liệu này")

    return ApiResponse(message="Chi tiết tài liệu", data=doc)


@router.delete("/{document_id}", response_model=ApiResponse)
def delete_document_endpoint(document_id: int, db: Session = Depends(get_db), current_user = Depends(get_current_user)):
    doc = get_document(db, document_id)
    if not doc:
        raise HTTPException(status_code=404, detail="Tài liệu không tồn tại")

    is_member = db.query(models.trip.TripMember).filter(
        models.trip.TripMember.trip_id == doc.trip_id,
        models.trip.TripMember.user_id == current_user.id,
    ).first()
    if not is_member:
        raise HTTPException(status_code=403, detail="Không có quyền xóa tài liệu này")

    deleted = delete_document(db, document_id)
    if not deleted:
        raise HTTPException(status_code=404, detail="Tài liệu không tồn tại")

    # Best-effort: remove uploaded file from disk if it's in /uploads.
    try:
        if isinstance(doc.url, str) and doc.url.startswith("/uploads/"):
            filename = doc.url.split("/")[-1]
            path = os.path.join(UPLOAD_DIR, filename)
            if os.path.isfile(path):
                os.remove(path)
    except Exception:
        pass

    return ApiResponse(message="Xóa tài liệu thành công", data=deleted)
