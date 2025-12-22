import uuid
from sqlalchemy import Column, Integer, String, DateTime, ForeignKey, Date
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from app.database import Base # Sửa dòng này (bỏ dấu chấm)

class Trip(Base):
    __tablename__ = "trips"
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, nullable=False)
    owner_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    start_date = Column(Date, nullable=True)
    end_date = Column(Date, nullable=True)
    base_currency = Column(String,default="VND")
    invite_code = Column(String, nullable=True, default=lambda: str(uuid.uuid4())[:8], index=True)   
    created_at = Column(DateTime(timezone=True), server_default=func.now())

    members = relationship("User", back_populates="trips", secondary="trip_members")

    itinerary_days = relationship("ItineraryDay", back_populates="trip", cascade="all, delete-orphan")
    
    settlements = relationship("Settlement", back_populates="trip")

    expenses = relationship("Expense", back_populates="trip", cascade="all, delete-orphan")
    
    documents = relationship("Document", back_populates="trip", cascade="all, delete-orphan")
    
    checklist_items = relationship("ChecklistItem", back_populates="trip", cascade="all, delete-orphan")
    
    exchange_rates = relationship("ExchangeRate", back_populates="trip", cascade="all, delete-orphan")
# Class TripMember giữ nguyên
class TripMember(Base):
    __tablename__ = "trip_members"
    id = Column(Integer, primary_key=True, index=True)
    trip_id = Column(Integer, ForeignKey("trips.id"), nullable=False)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    role = Column(String, default="member")
    status = Column(String, default="joined")
