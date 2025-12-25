from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from app.database import get_db
from app.schemas.user import UserRead
from app.schemas.response import ApiResponse
from app.crud.crud import get_user_by_email, get_user_by_id, update_user_profile
from app.dependencies import get_current_user
from pydantic import BaseModel

router = APIRouter(prefix="/users", tags=["users"])

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

@router.put("/me", response_model=ApiResponse)
def update_profile(profile_data: UpdateProfileRequest, db: Session = Depends(get_db), current_user = Depends(get_current_user)):
    updated_user = update_user_profile(db, current_user.id, profile_data.name, profile_data.avatar_url)
    if not updated_user:
        raise HTTPException(404, "Người dùng không tồn tại")
    return ApiResponse(message="Cập nhật thông tin thành công", data=updated_user)
