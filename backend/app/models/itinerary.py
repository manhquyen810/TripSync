from sqlalchemy import Column, Integer, String, Boolean, ForeignKey, Text, DateTime, Time, UniqueConstraint
from sqlalchemy.sql import func
from app.database import Base
from sqlalchemy import Time
from sqlalchemy.orm import relationship
class ItineraryDay(Base):
    __tablename__ = "itinerary_days" 
    id = Column(Integer, primary_key=True, index=True)
    trip_id = Column(Integer, ForeignKey("trips.id"), nullable=False)
    day_number = Column(Integer, nullable=False)

    trip = relationship("Trip", back_populates="itinerary_days")
    activities = relationship("Activity", back_populates="day", cascade="all, delete-orphan")
class Activity(Base):
    __tablename__ = "activities"
    id = Column(Integer, primary_key=True, index=True)
    day_id = Column(Integer, ForeignKey("itinerary_days.id"), nullable=False)
    title = Column(String, nullable=False)
    description = Column(Text, nullable=True)
    location = Column(String, nullable=True)
    location_lat = Column(String, nullable=True)
    location_long = Column(String, nullable=True)
    start_time = Column(Time, nullable=True) 
    is_confirmed = Column(Boolean, default=False)
    created_by = Column(Integer, ForeignKey("users.id"), nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())

    day = relationship("ItineraryDay", back_populates="activities")
    # [MỚI] Thêm dòng này để truy cập được danh sách vote của hoạt động
    votes = relationship("ActivityVote", back_populates="activity", cascade="all, delete-orphan")
class ActivityVote(Base):
    __tablename__ = "activity_votes"
    id = Column(Integer, primary_key=True, index=True)
    activity_id = Column(Integer, ForeignKey("activities.id"), nullable=False)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    vote = Column(String, default="upvote") 
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    # [MỚI] Thêm dòng này để truy cập ngược lại activity từ 1 vote
    activity = relationship("Activity", back_populates="votes")

    # [MỚI] Ràng buộc: 1 User chỉ được vote 1 lần cho 1 Activity
    __table_args__ = (UniqueConstraint('activity_id', 'user_id', name='_user_activity_uc'),)