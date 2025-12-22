from pydantic import BaseModel, EmailStr, constr

class Token(BaseModel):
    access_token: str
    token_type: str = "bearer"

class TokenPayload(BaseModel):
    sub: str | None = None

# Forgot Password Schemas
class ForgotPasswordRequest(BaseModel):
    email: EmailStr

class VerifyOtpRequest(BaseModel):
    email: EmailStr
    otp: constr(min_length=5, max_length=5)

class ResetPasswordRequest(BaseModel):
    email: EmailStr
    otp: constr(min_length=5, max_length=5)
    new_password: constr(min_length=6, max_length=128)