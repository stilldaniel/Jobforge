from datetime import datetime

from pydantic import BaseModel


class NotificationResponse(BaseModel):
    id: int
    user_id: int
    job_match_id: int
    notification_type: str
    status: str
    title: str
    message: str | None
    created_at: datetime
    sent_at: datetime | None
    read_at: datetime | None

    class Config:
        from_attributes = True