from pydantic import BaseModel
from datetime import datetime

class ExchangeRateCreate(BaseModel):
    trip_id: int
    from_currency: str
    to_currency: str
    rate: float

class ExchangeRateRead(BaseModel):
    id: int
    trip_id: int
    from_currency: str
    to_currency: str
    rate: float
    created_by: int
    created_at: datetime

    class Config:
        orm_mode = True
