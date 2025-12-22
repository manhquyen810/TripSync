from pydantic import BaseModel, constr, validator
from datetime import date
from typing import Optional, TypeAlias

TripName: TypeAlias = constr(strip_whitespace=True, min_length=1, max_length=200)
CurrencyCode: TypeAlias = constr(strip_whitespace=True, regex=r"^[A-Z]{3}$")
InviteCode: TypeAlias = constr(strip_whitespace=True, min_length=1, max_length=64)

class TripCreate(BaseModel):
    name: TripName
    start_date: Optional[date] = None
    end_date: Optional[date] = None
    base_currency: CurrencyCode = "VND"
    invite_code: Optional[InviteCode] = None

    @validator("end_date")
    def _validate_date_range(cls, end_date: Optional[date], values):
        start_date = values.get("start_date")
        if start_date and end_date and end_date < start_date:
            raise ValueError("Ngày kết thúc phải lớn hơn hoặc bằng ngày bắt đầu")
        return end_date

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