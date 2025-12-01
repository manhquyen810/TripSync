from passlib.context import CryptContext
from datetime import datetime, timedelta, timezone
from jwt import encode, decode
from jwt.exceptions import PyJWTError
from app.config import SECRET_KEY, ACCESS_TOKEN_EXPIRE_MINUTES
from typing import Optional

pwd_context = CryptContext(
    schemes=["argon2"],
    deprecated="auto",
)

def get_password_hash(password: str) -> str:
    return pwd_context.hash(password)

def verify_password(plain: str, hashed: str) -> bool:
    return pwd_context.verify(plain, hashed)

def create_access_token(data: dict, expires_delta: Optional[timedelta] = None) -> str:
    to_encode = data.copy()

    expire = datetime.now(timezone.utc) + (
        expires_delta or timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    )
    to_encode.update({"exp": expire})

    return encode(to_encode, SECRET_KEY, algorithm="HS256")

def decode_access_token(token: str):
    try:
        payload = decode(token, SECRET_KEY, algorithms=["HS256"])
        return payload
    except PyJWTError:
        return None
