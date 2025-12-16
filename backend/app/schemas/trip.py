from pydantic import BaseModel
from datetime import date
from typing import Optional

class TripCreate(BaseModel):
    name: str
    start_date: Optional[date] = None
    end_date: Optional[date] = None
    base_currency: Optional[str] = "VND"
    invite_code: Optional[str] = None

class TripRead(BaseModel):
    id: int
    name: str
    owner_id: int
    start_date: Optional[date] = None
    end_date: Optional[date] = None
    base_currency: str = "VND"
    invite_code: Optional[str] = None

    class Config:
        orm_mode = True