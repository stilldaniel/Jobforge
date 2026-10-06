from datetime import datetime

from pydantic import BaseModel, ConfigDict


class NotificationResponse(BaseModel):
    id: int
    user_id: int
    job_match_id: int
    notification_type: str
    channel: str
    status: str
    title: str
    message: str | None
    attempts: int
    last_error: str | None
    created_at: datetime
    sent_at: datetime | None
    read_at: datetime | None

    model_config = ConfigDict(from_attributes=True)