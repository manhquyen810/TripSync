from pydantic import BaseModel
from typing import Optional, List
from datetime import datetime

# --- Expense Schemas ---
class ExpenseCreate(BaseModel):
    trip_id: int
    amount: float
    currency: str = "VND"
    description: Optional[str] = None
    split_method: str = "equal"
    expense_date: Optional[datetime] = None

    involved_user_ids: List[int] # Danh sách user_id tham gia chia sẻ chi phí

class ExpenseRead(BaseModel):
    id: int
    trip_id: int
    payer_id: int
    amount: float
    currency: str
    description: Optional[str] = None
    split_method: str
    expense_date: Optional[datetime]

    class Config:
        orm_mode = True

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
        orm_mode = True