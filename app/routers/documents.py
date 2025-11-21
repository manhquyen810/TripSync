from fastapi import APIRouter, Depends, UploadFile, File, HTTPException
from sqlalchemy.orm import Session
from app.database import get_db
from app.dependencies import get_current_user
import os
from app.config import UPLOAD_DIR
from uuid import uuid4
from app.crud.crud import create_document, list_documents_for_trip
from app.schemas.document import DocumentRead
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
