from pydantic import BaseModel, EmailStr

class EmailSend(BaseModel):
    to_email: EmailStr
    subject: str
    body: str
