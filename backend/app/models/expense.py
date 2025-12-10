from sqlalchemy import Column, Integer, Float, String, ForeignKey, DateTime, Boolean
from sqlalchemy.sql import func
from app.database import Base
from sqlalchemy.orm import relationship
class Expense(Base):
    __tablename__ = "expenses"
    id = Column(Integer, primary_key=True, index=True)
    trip_id = Column(Integer, ForeignKey("trips.id"), nullable=False)
    payer_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    amount = Column(Float, nullable=False)
    currency = Column(String, default="VND")
    description = Column(String, nullable=True)
    expense_date = Column(DateTime(timezone=True), nullable=False)
    split_method = Column(String, default="equal")
    created_at = Column(DateTime(timezone=True), server_default=func.now())

    trip = relationship("Trip", back_populates="expenses")
    payer = relationship("User", foreign_keys=[payer_id])
    splits = relationship("ExpenseSplit", back_populates="expense", cascade="all, delete-orphan")
class ExpenseSplit(Base):
    __tablename__ = "expense_splits"
    id = Column(Integer, primary_key=True, index=True)
    expense_id = Column(Integer, ForeignKey("expenses.id"), nullable=False)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    amount = Column(Float, nullable=False)

    expense = relationship("Expense", back_populates="splits")
    user = relationship("User", foreign_keys=[user_id])
    
class Settlement(Base):
    __tablename__ = "settlements"
    id = Column(Integer, primary_key=True, index=True)
    trip_id = Column(Integer, ForeignKey("trips.id"), nullable=False)
    payer_id = Column(Integer, ForeignKey("users.id"), nullable=False)   # Người trả nợ (người chuyển tiền)
    receiver_id = Column(Integer, ForeignKey("users.id"), nullable=False) # Người nhận nợ (chủ nợ)
    amount = Column(Float, nullable=False) # Số tiền trả
    created_at = Column(DateTime(timezone=True), server_default=func.now())

    trip = relationship("Trip", back_populates="settlements")
    payer = relationship("User", foreign_keys=[payer_id])
    receiver = relationship("User", foreign_keys=[receiver_id])