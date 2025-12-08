from sqlalchemy import Column, Integer, String, Boolean, DateTime, func
from app.database import Base
from sqlalchemy.orm import relationship

class User(Base):
    __tablename__ = "users"
    id = Column(Integer, primary_key=True, index=True)
    email = Column(String, unique=True, index=True, nullable=False)
    hashed_password = Column(String, nullable=False)
    name = Column(String, nullable=False)
    avatar_url = Column(String, nullable=True) 
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())

    trips = relationship("Trip", back_populates="members", secondary="trip_members")
    expenses_paid = relationship("Expense", back_populates="payer")
    expenses_splits = relationship("ExpenseSplit", back_populates="user")
    settlements_paid = relationship("Settlement", back_populates="payer", foreign_keys="[Settlement.payer_id]")
    settlements_received = relationship("Settlement", back_populates="receiver", foreign_keys="[Settlement.receiver_id]")