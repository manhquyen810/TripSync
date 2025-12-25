from pydantic import BaseModel
from typing import Optional
from datetime import time, datetime

# --- Activity Schemas ---
class ActivityCreate(BaseModel):
    day_id: int
    title: str
    description: Optional[str] = None
    location: Optional[str] = None
    location_lat: Optional[str] = None
    location_long: Optional[str] = None
    start_time: Optional[time] = None 

class ActivityRead(BaseModel):
    id: int
    day_id: int
    create_by: int
    title: str
    description: Optional[str] = None
    location: Optional[str] = None
    location_lat: Optional[str] = None
    location_long: Optional[str] = None
    start_time: Optional[time] = None
    is_confirmed: bool
    created_at: datetime

    class Config:
        orm_mode = True