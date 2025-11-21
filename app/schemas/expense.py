from pydantic import BaseModel
from typing import Optional
from datetime import datetime

# --- Expense Schemas ---
class ExpenseCreate(BaseModel):
    trip_id: int
    amount: float
    currency: str = "VND"
    description: Optional[str] = None
    split_method: str = "equal"

class ExpenseRead(BaseModel):
    id: int
    trip_id: int
    payer_id: int
    amount: float
    currency: str
    description: Optional[str] = None
    split_method: str

    class Config:
        from_attributes = True

# --- Settlement Schemas (Mới) ---
class SettlementCreate(BaseModel):
    trip_id: int
    receiver_id: int
    amount: float

class SettlementRead(BaseModel):
    id: int
    trip_id: int
    payer_id: int
    receiver_id: int
    amount: float
    created_at: datetime

    class Config:
        from_attributes = True