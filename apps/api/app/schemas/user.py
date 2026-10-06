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

class NotificationPreferences(BaseModel):
    job_alerts_enabled: bool
    high_match_alerts_enabled: bool
    digest_notifications_enabled: bool
    email_notifications_enabled: bool

    model_config = ConfigDict(from_attributes=True)


class NotificationPreferencesUpdate(BaseModel):
    """
    Partial update: only the preferences that are sent are changed.
    """

    job_alerts_enabled: bool | None = None
    high_match_alerts_enabled: bool | None = None
    digest_notifications_enabled: bool | None = None
    email_notifications_enabled: bool | None = None
