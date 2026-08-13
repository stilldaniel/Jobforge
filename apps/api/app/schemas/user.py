from datetime import datetime

from pydantic import BaseModel, ConfigDict, EmailStr


class UserCreate(BaseModel):
    email: EmailStr
    full_name: str | None = None
    timezone: str = "UTC"


class UserResponse(BaseModel):
    id: int
    email: EmailStr
    full_name: str | None
    timezone: str
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)