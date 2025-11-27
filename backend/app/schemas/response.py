from pydantic import BaseModel
from typing import Optional, Any

class ApiResponse(BaseModel):
    message: str
    data: Optional[Any] = None