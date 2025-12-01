from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordRequestForm # <--- Import quan trọng để fix lỗi Auth Swagger
from sqlalchemy.orm import Session
from app.schemas.user import UserCreate, UserRead
from app.schemas.response import ApiResponse
from app.crud.crud import get_user_by_email, create_user, authenticate_user
from app.database import get_db
from app.core.security import create_access_token
from datetime import timedelta
from app.config import ACCESS_TOKEN_EXPIRE_MINUTES

router = APIRouter(prefix="/auth", tags=["auth"])

@router.post("/register", response_model=ApiResponse)
def register(user_in: UserCreate, db: Session = Depends(get_db)):
    existing = get_user_by_email(db, user_in.email)
    if existing:
        raise HTTPException(status_code=400, detail="Email already registered")
    
    user = create_user(db, user=user_in) 
    
    return ApiResponse(
        message="Đăng kí thành công!", 
        data=UserRead.from_orm(user) 
    )

@router.post("/login", response_model=ApiResponse)
def login(form_data: OAuth2PasswordRequestForm = Depends(), db: Session = Depends(get_db)):
    # Swagger gửi email vào trường 'username', nên ta lấy form_data.username
    user = authenticate_user(db, form_data.username, form_data.password)
    
    if not user:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Email hoặc mật khẩu sai")
    
    access_token = create_access_token(
        data={"sub": str(user.id)}, 
        expires_delta=timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    )
    
    return ApiResponse(message="Đăng nhập thành công!", data={"access_token": access_token, "token_type": "bearer"})

@router.post("/token", include_in_schema=False)
def login_for_swagger(form_data: OAuth2PasswordRequestForm = Depends(), db: Session = Depends(get_db)):
    user = authenticate_user(db, form_data.username, form_data.password)
    
    if not user:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Email hoặc mật khẩu sai")
    
    access_token = create_access_token(
        data={"sub": str(user.id)}, 
        expires_delta=timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    )
    
    # Return dict phẳng, không bọc trong ApiResponse hay data
    return {"access_token": access_token, "token_type": "bearer"}