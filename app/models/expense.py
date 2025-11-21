from sqlalchemy import Column, Integer, Float, String, ForeignKey, DateTime, Boolean
from sqlalchemy.sql import func
from app.database import Base

class Expense(Base):
    __tablename__ = "expenses"
    id = Column(Integer, primary_key=True, index=True)
    trip_id = Column(Integer, ForeignKey("trips.id"), nullable=False)
    payer_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    amount = Column(Float, nullable=False)
    currency = Column(String, default="VND")
    description = Column(String, nullable=True)
    split_method = Column(String, default="equal") # <--- THÊM (equal, exact, percent)
    created_at = Column(DateTime(timezone=True), server_default=func.now())

class ExpenseSplit(Base):
    __tablename__ = "expense_splits"
    id = Column(Integer, primary_key=True, index=True)
    expense_id = Column(Integer, ForeignKey("expenses.id"), nullable=False)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    amount = Column(Float, nullable=False)
    
class Settlement(Base):
    __tablename__ = "settlements"
    id = Column(Integer, primary_key=True, index=True)
    trip_id = Column(Integer, ForeignKey("trips.id"), nullable=False)
    payer_id = Column(Integer, ForeignKey("users.id"), nullable=False)   # Người trả nợ (người chuyển tiền)
    receiver_id = Column(Integer, ForeignKey("users.id"), nullable=False) # Người nhận nợ (chủ nợ)
    amount = Column(Float, nullable=False) # Số tiền trả
    created_at = Column(DateTime(timezone=True), server_default=func.now())