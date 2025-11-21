from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from app.database import get_db
from app.schemas.user import UserRead
from app.schemas.response import ApiResponse
from app.crud.crud import get_user_by_email
from app.dependencies import get_current_user
router = APIRouter(prefix="/users", tags=["users"])

@router.get("/me", response_model=ApiResponse)
def me(current_user = Depends(get_current_user)):
    return ApiResponse(message="Thông tin người dùng", data=current_user)
