from pydantic import BaseModel
from typing import Optional
from datetime import time

# --- Activity Schemas ---
class ActivityCreate(BaseModel):
    day_id: int
    title: str
    description: Optional[str] = None
    location: Optional[str] = None
    start_time: Optional[time] = None 

class ActivityRead(BaseModel):
    id: int
    day_id: int
    title: str
    description: Optional[str] = None
    location: Optional[str] = None
    start_time: Optional[time] = None
    is_confirmed: bool

    class Config:
        from_attributes = True