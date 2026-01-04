from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordRequestForm # <--- Import quan trọng để fix lỗi Auth Swagger
from sqlalchemy.orm import Session
from app.schemas.user import UserCreate, UserRead
from app.schemas.auth import ForgotPasswordRequest, VerifyOtpRequest, ResetPasswordRequest
from app.schemas.response import ApiResponse
from app.crud.crud import get_user_by_email, create_user, authenticate_user, update_user_otp, verify_user_otp, reset_user_password
from app.database import get_db
from app.core.security import create_access_token
from app.services.email_service import send_otp_email
from datetime import timedelta, datetime, timezone
from app.config import ACCESS_TOKEN_EXPIRE_MINUTES, OTP_EXPIRE_MINUTES
import random

router = APIRouter(prefix="/auth", tags=["auth"])

@router.post("/register", response_model=ApiResponse)
def register(user_in: UserCreate, db: Session = Depends(get_db)):
    existing = get_user_by_email(db, user_in.email)
    if existing:
        raise HTTPException(status_code=400, detail="Email đã được đăng ký")
    
    user = create_user(db, user=user_in) 
    
    return ApiResponse(
        message="Đăng kí thành công!", 
        data=UserRead.from_orm(user) 
    )

@router.post("/login", response_model=ApiResponse)
def login(form_data: OAuth2PasswordRequestForm = Depends(), db: Session = Depends(get_db)):
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
    return {"access_token": access_token, "token_type": "bearer"}

@router.post("/forgot-password", response_model=ApiResponse)
def forgot_password(request: ForgotPasswordRequest, db: Session = Depends(get_db)):
    """Send OTP to email for password reset"""
    user = get_user_by_email(db, request.email)
    if not user:
        raise HTTPException(status_code=404, detail="Email không tồn tại trong hệ thống")
    
    # Generate 5-digit OTP
    otp_code = ''.join([str(random.randint(0, 9)) for _ in range(5)])
    
    # Set OTP expiration
    otp_expires_at = datetime.now(timezone.utc) + timedelta(minutes=OTP_EXPIRE_MINUTES)
    
    # Update user with OTP
    update_user_otp(db, request.email, otp_code, otp_expires_at)
    
    # Send OTP via email
    if not send_otp_email(request.email, otp_code):
        raise HTTPException(status_code=500, detail="Không thể gửi email. Vui lòng thử lại sau")
    
    return ApiResponse(
        message=f"Mã OTP đã được gửi đến {request.email}",
        data={"email": request.email}
    )

@router.post("/verify-otp", response_model=ApiResponse)
def verify_otp(request: VerifyOtpRequest, db: Session = Depends(get_db)):
    """Verify OTP code"""
    user = verify_user_otp(db, request.email, request.otp)
    
    if not user:
        raise HTTPException(status_code=400, detail="Mã OTP không hợp lệ hoặc đã hết hạn")
    
    return ApiResponse(
        message="Xác minh OTP thành công",
        data={"email": request.email, "verified": True}
    )

@router.post("/reset-password", response_model=ApiResponse)
def reset_password(request: ResetPasswordRequest, db: Session = Depends(get_db)):
    """Reset password with OTP verification"""
    # Verify OTP first
    user = verify_user_otp(db, request.email, request.otp)
    
    if not user:
        raise HTTPException(status_code=400, detail="Mã OTP không hợp lệ hoặc đã hết hạn")
    
    # Reset password
    reset_user_password(db, request.email, request.new_password)
    
    return ApiResponse(
        message="Đặt lại mật khẩu thành công",
        data={"email": request.email}
    )