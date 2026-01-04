from fastapi import APIRouter, Depends, UploadFile, File, HTTPException
from sqlalchemy.orm import Session
from app.database import get_db
from app.dependencies import get_current_user
import os
from app.config import UPLOAD_DIR
from uuid import uuid4
from app import models
from app.crud.crud import create_document, list_documents_for_trip, get_document, delete_document
from app.schemas.response import ApiResponse  # Thêm dòng này

router = APIRouter(prefix="/documents", tags=["documents"])

os.makedirs(UPLOAD_DIR, exist_ok=True)

@router.post("/upload", response_model=ApiResponse)
async def upload(trip_id: int, category: str | None = None, file: UploadFile = File(...), db: Session = Depends(get_db), current_user = Depends(get_current_user)):
    ext = os.path.splitext(file.filename)[1]
    name = f"{uuid4().hex}{ext}"
    path = os.path.join(UPLOAD_DIR, name)
    with open(path, "wb") as f:
        content = await file.read()
        f.write(content)
    url = f"/uploads/{name}"  # static mount in main
    doc = create_document(db, trip_id=trip_id, uploader_id=current_user.id, filename=file.filename, url=url, category=category)
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
