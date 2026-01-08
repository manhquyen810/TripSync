from pydantic import BaseModel

class DeviceTokenCreate(BaseModel):
    device_token: str
