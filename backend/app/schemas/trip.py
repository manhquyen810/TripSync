from pydantic import BaseModel, Field, validator
from datetime import date
from typing import Optional

class TripCreate(BaseModel):
    name: str = Field(..., min_length=1, max_length=200)
    destination: Optional[str] = Field(None, min_length=1, max_length=200)
    description: Optional[str] = Field(None, min_length=1, max_length=2000)
    start_date: Optional[date] = None
    end_date: Optional[date] = None
    base_currency: str = Field("VND", regex=r"^[A-Z]{3}$")
    invite_code: Optional[str] = Field(None, min_length=1, max_length=64)

    @validator("end_date")
    def _validate_date_range(cls, end_date: Optional[date], values):
        start_date = values.get("start_date")
        if start_date and end_date and end_date < start_date:
            raise ValueError("Ngày kết thúc phải lớn hơn hoặc bằng ngày bắt đầu")
        return end_date


class TripUpdate(BaseModel):
    name: Optional[str] = Field(None, min_length=1, max_length=200)
    destination: Optional[str] = Field(None, min_length=1, max_length=200)
    description: Optional[str] = Field(None, min_length=1, max_length=2000)
    start_date: Optional[date] = None
    end_date: Optional[date] = None
    base_currency: Optional[str] = Field(None, regex=r"^[A-Z]{3}$")
    invite_code: Optional[str] = Field(None, min_length=1, max_length=64)

    @validator("end_date")
    def _validate_date_range(cls, end_date: Optional[date], values):
        start_date = values.get("start_date")
        if start_date and end_date and end_date < start_date:
            raise ValueError("Ngày kết thúc phải lớn hơn hoặc bằng ngày bắt đầu")
        return end_date

class TripRead(BaseModel):
    id: int
    name: str
    destination: Optional[str] = None
    description: Optional[str] = None
    owner_id: int
    start_date: Optional[date] = None
    end_date: Optional[date] = None
    base_currency: str = "VND"
    invite_code: Optional[str] = None

    class Config:
        orm_mode = True