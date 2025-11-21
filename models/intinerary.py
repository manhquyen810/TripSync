from sqlalchemy import Column, Integer, String, Boolean, ForeignKey, Text, DateTime
from sqlalchemy.sql import func
from app.database import Base
from sqlalchemy import Time
class ItineraryDay(Base):
    __tablename__ = "itinerary_days" # Đã fix dấu gạch dưới
    id = Column(Integer, primary_key=True, index=True)
    trip_id = Column(Integer, ForeignKey("trips.id"), nullable=False)
    day_number = Column(Integer, nullable=False)

class Activity(Base):
    __tablename__ = "activities"
    id = Column(Integer, primary_key=True, index=True)
    day_id = Column(Integer, ForeignKey("itinerary_days.id"), nullable=False)
    title = Column(String, nullable=False)
    description = Column(Text, nullable=True)
    location = Column(String, nullable=True)
    start_time = Column(Time, nullable=True) # <--- THÊM (Để sort: Sáng/Trưa/Chiều)
    is_confirmed = Column(Boolean, default=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now())

class ActivityVote(Base):
    __tablename__ = "activity_votes"
    id = Column(Integer, primary_key=True, index=True)
    activity_id = Column(Integer, ForeignKey("activities.id"), nullable=False)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    vote = Column(String, default="upvote") # Đã fix default value khớp với String
    created_at = Column(DateTime(timezone=True), server_default=func.now())