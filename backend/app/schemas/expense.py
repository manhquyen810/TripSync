from datetime import datetime
from typing import Literal, Optional, TypeAlias

from pydantic import BaseModel, Field, PositiveFloat, conint, conlist, constr

TripId: TypeAlias = conint(gt=0)
UserId: TypeAlias = conint(gt=0)
CurrencyCode: TypeAlias = constr(strip_whitespace=True, regex=r"^[A-Z]{3}$")
DescriptionStr: TypeAlias = constr(strip_whitespace=True, max_length=500)
InvolvedUserIds: TypeAlias = conlist(UserId, min_items=1)

# --- Expense Schemas ---
class ExpenseCreate(BaseModel):
    trip_id: TripId
    amount: PositiveFloat
    currency: CurrencyCode = "VND"
    description: Optional[DescriptionStr] = None
    split_method: Literal["equal"] = "equal"
    expense_date: datetime = Field(default_factory=datetime.utcnow)

    involved_user_ids: InvolvedUserIds

class ExpenseRead(BaseModel):
    id: int
    trip_id: int
    payer_id: int
    amount: float
    currency: str
    description: Optional[str] = None
    split_method: str
    expense_date: datetime

    class Config:
        orm_mode = True

# --- Nested schemas for detailed response ---
class UserBasic(BaseModel):
    id: int
    name: str
    avatar_url: Optional[str] = None

    class Config:
        orm_mode = True

class ExpenseSplitRead(BaseModel):
    user_id: int
    amount_owed: float
    user: UserBasic

    class Config:
        orm_mode = True

class ExpenseDetailRead(BaseModel):
    id: int
    trip_id: int
    payer_id: int
    amount: float
    currency: str
    description: Optional[str] = None
    split_method: str
    expense_date: datetime
    created_at: datetime
    payer: UserBasic
    splits: list[ExpenseSplitRead]

    class Config:
        orm_mode = True

# --- Settlement Schemas (Mới) ---
class SettlementCreate(BaseModel):
    trip_id: TripId
    receiver_id: UserId
    amount: PositiveFloat

class SettlementRead(BaseModel):
    id: int
    trip_id: int
    payer_id: int
    receiver_id: int
    amount: float
    created_at: datetime

    class Config:
        orm_mode = True