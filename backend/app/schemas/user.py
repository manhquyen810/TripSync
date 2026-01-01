from pydantic import BaseModel, EmailStr, constr
from typing import Optional

# --- THÊM CLASS NÀY ---
class UserLogin(BaseModel):
    email: EmailStr
    password: constr(min_length=6, max_length=128)
# ----------------------

class UserCreate(BaseModel):
    email: EmailStr
    password: constr(min_length=6, max_length=128)
    name: constr(strip_whitespace=True, min_length=1, max_length=100)  # Bắt buộc

class UserRead(BaseModel):
    id: int
    email: EmailStr
    name: str
    is_active: bool

    class Config:
        from_attributes = True