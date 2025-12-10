from sqlalchemy import Column, Integer, String, ForeignKey, Boolean
from sqlalchemy.sql import func
from sqlalchemy import DateTime
from app.database import Base
from sqlalchemy.orm import relationship
class ChecklistItem(Base):
    __tablename__ = "checklist_items"
    id = Column(Integer, primary_key=True, index=True)
    trip_id = Column(Integer, ForeignKey("trips.id"), nullable=False)
    content = Column(String, nullable=False)
    assignee = Column(Integer, ForeignKey("users.id"), nullable=True)
    is_done = Column(Boolean, default=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now())

    trip = relationship("Trip", back_populates="checklist_items")