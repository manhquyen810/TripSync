from pydantic import BaseModel, EmailStr
from typing import Optional

# --- THÊM CLASS NÀY ---
class UserLogin(BaseModel):
    email: EmailStr
    password: str
# ----------------------

class UserCreate(BaseModel):
    email: EmailStr
    password: str
    name: str  # Bắt buộc

class UserRead(BaseModel):
    id: int
    email: EmailStr
    name: str
    is_active: bool

    class Config:
        from_attributes = True