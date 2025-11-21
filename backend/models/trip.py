from sqlalchemy import Column, Integer, String, DateTime, ForeignKey, Date
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from app.database import Base # Sửa dòng này (bỏ dấu chấm)

class Trip(Base):
    __tablename__ = "trips"
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, nullable=False)
    owner_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    start_date = Column(Date, nullable=True) # <--- THÊM
    end_date = Column(Date, nullable=True)   # <--- THÊM
    created_at = Column(DateTime(timezone=True), server_default=func.now())

# Class TripMember giữ nguyên
class TripMember(Base):
    __tablename__ = "trip_members"
    id = Column(Integer, primary_key=True, index=True)
    trip_id = Column(Integer, ForeignKey("trips.id"), nullable=False)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    role = Column(String, default="member")