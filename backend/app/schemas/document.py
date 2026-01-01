from pydantic import BaseModel

class DocumentRead(BaseModel):
    id: int
    trip_id: int
    uploader_id: int
    filename: str
    url: str
    category: str | None = None

    class Config:
        from_attributes = True
