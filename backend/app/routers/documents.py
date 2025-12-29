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
from app.crud.crud import create_document, list_documents_for_trip
from app.schemas.document import DocumentRead
from app.schemas.response import ApiResponse  # Thêm dòng này
import io

router = APIRouter(prefix="/documents", tags=["documents"])

os.makedirs(UPLOAD_DIR, exist_ok=True)

@router.post("/upload", response_model=ApiResponse)
async def upload(trip_id: int, category: str | None = None, file: UploadFile = File(...), db: Session = Depends(get_db), current_user = Depends(get_current_user)):
    # Validate file size (max 10MB)
    MAX_FILE_SIZE = 10 * 1024 * 1024  # 10MB
    content = await file.read()
    if len(content) > MAX_FILE_SIZE:
        raise HTTPException(400, "File quá lớn. Kích thước tối đa là 10MB")
    
    # Validate file type
    allowed_extensions = {'.pdf', '.jpg', '.jpeg', '.png', '.doc', '.docx', '.txt'}
    ext = os.path.splitext(file.filename)[1].lower()
    if ext not in allowed_extensions:
        raise HTTPException(400, f"Định dạng file không được hỗ trợ. Chỉ cho phép: {', '.join(allowed_extensions)}")
    
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

            folder = "tripsync"
            if trip_id:
                folder = f"{folder}/trip_{trip_id}"
            if category:
                folder = f"{folder}/{category}"

            public_id = uuid4().hex
            upload_result = cloudinary.uploader.upload(
                io.BytesIO(content),
                resource_type="auto",
                folder=folder,
                public_id=public_id,
                overwrite=False,
            )

            secure_url = upload_result.get("secure_url")
            if not secure_url:
                raise RuntimeError("Cloudinary upload did not return secure_url")
            url = str(secure_url)
        except Exception as e:
            raise HTTPException(500, f"Upload Cloudinary thất bại: {e}")
    else:
        name = f"{uuid4().hex}{ext}"
        path = os.path.join(UPLOAD_DIR, name)
        with open(path, "wb") as f:
            f.write(content)

        url = f"/uploads/{name}"
    doc = create_document(db, trip_id=trip_id, uploader_id=current_user.id, filename=file.filename, url=url, category=category)
    return ApiResponse(message="Tải lên thành công", data=doc)

@router.get("/trip/{trip_id}", response_model=ApiResponse)
def list_docs(trip_id: int, db: Session = Depends(get_db), current_user = Depends(get_current_user)):
    docs = list_documents_for_trip(db, trip_id)
    return ApiResponse(message="Danh sách tài liệu", data=docs)

@router.get("/{document_id}", response_model=ApiResponse)
def get_document(document_id: int, db: Session = Depends(get_db), current_user = Depends(get_current_user)):
    from app.crud.crud import get_document_by_id
    document = get_document_by_id(db, document_id)
    if not document:
        raise HTTPException(404, "Tài liệu không tồn tại")
    return ApiResponse(message="Chi tiết tài liệu", data=document)

@router.delete("/{document_id}", response_model=ApiResponse)
def delete_document_endpoint(document_id: int, db: Session = Depends(get_db), current_user = Depends(get_current_user)):
    from app.crud.crud import delete_document
    from app.models.document import Document
    document = db.query(Document).filter(Document.id == document_id).first()
    if not document:
        raise HTTPException(404, "Tài liệu không tồn tại")
    if document.uploader_id != current_user.id:
        raise HTTPException(403, "Chỉ người upload mới có thể xóa tài liệu")
    # Delete file from filesystem
    if os.path.exists(os.path.join(UPLOAD_DIR, os.path.basename(document.url))):
        os.remove(os.path.join(UPLOAD_DIR, os.path.basename(document.url)))
    delete_document(db, document_id)
    return ApiResponse(message="Xóa tài liệu thành công", data=None)
