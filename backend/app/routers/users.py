from fastapi import APIRouter, Depends, HTTPException, UploadFile, File
from sqlalchemy.orm import Session
from app.database import get_db
from app.schemas.user import UserRead
from app.schemas.response import ApiResponse
from app.crud.crud import get_user_by_email, get_user_by_id, update_user_profile
from app.dependencies import get_current_user
from pydantic import BaseModel
from app.config import (
    UPLOAD_DIR,
    CLOUDINARY_ENABLED,
    CLOUDINARY_URL,
    CLOUDINARY_CLOUD_NAME,
    CLOUDINARY_API_KEY,
    CLOUDINARY_API_SECRET,
)

import io
import os
from uuid import uuid4

router = APIRouter(prefix="/users", tags=["users"])

os.makedirs(UPLOAD_DIR, exist_ok=True)

@router.get("/me", response_model=ApiResponse)
def me(current_user = Depends(get_current_user)):
    return ApiResponse(message="Thông tin người dùng", data=current_user)

@router.get("/{user_id}", response_model=ApiResponse)
def get_user(user_id: int, db: Session = Depends(get_db), current_user = Depends(get_current_user)):
    user = get_user_by_id(db, user_id)
    if not user:
        raise HTTPException(404, "Người dùng không tồn tại")
    return ApiResponse(message="Thông tin người dùng", data=user)

class UpdateProfileRequest(BaseModel):
    name: str
    avatar_url: str = None


@router.post("/me/avatar", response_model=ApiResponse)
async def upload_avatar(
    file: UploadFile = File(...),
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user),
):
    # Validate file size (max 10MB)
    MAX_FILE_SIZE = 10 * 1024 * 1024
    content = await file.read()
    if len(content) > MAX_FILE_SIZE:
        raise HTTPException(400, "File quá lớn. Kích thước tối đa là 10MB")

    # Validate file type (image only)
    allowed_extensions = {".jpg", ".jpeg", ".png", ".webp"}
    ext = os.path.splitext(file.filename or "")[1].lower()
    if ext not in allowed_extensions:
        raise HTTPException(
            400,
            f"Định dạng file không được hỗ trợ. Chỉ cho phép: {', '.join(sorted(allowed_extensions))}",
        )

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

            folder = f"tripsync/avatars/user_{current_user.id}"
            public_id = uuid4().hex
            upload_result = cloudinary.uploader.upload(
                io.BytesIO(content),
                resource_type="image",
                folder=folder,
                public_id=public_id,
                overwrite=True,
            )

            secure_url = upload_result.get("secure_url")
            if not secure_url:
                raise RuntimeError("Cloudinary upload did not return secure_url")
            url = str(secure_url)
        except Exception as e:
            raise HTTPException(500, f"Upload Cloudinary thất bại: {e}")
    else:
        name = f"avatar_{current_user.id}_{uuid4().hex}{ext}"
        path = os.path.join(UPLOAD_DIR, name)
        with open(path, "wb") as f:
            f.write(content)
        url = f"/uploads/{name}"

    # Persist avatar URL on user
    updated_user = update_user_profile(db, current_user.id, current_user.name, url)
    if not updated_user:
        raise HTTPException(404, "Người dùng không tồn tại")

    return ApiResponse(message="Tải avatar thành công", data={"url": url})

@router.put("/me", response_model=ApiResponse)
def update_profile(profile_data: UpdateProfileRequest, db: Session = Depends(get_db), current_user = Depends(get_current_user)):
    updated_user = update_user_profile(db, current_user.id, profile_data.name, profile_data.avatar_url)
    if not updated_user:
        raise HTTPException(404, "Người dùng không tồn tại")
    return ApiResponse(message="Cập nhật thông tin thành công", data=updated_user)
