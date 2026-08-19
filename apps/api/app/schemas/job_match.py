from datetime import datetime

from pydantic import BaseModel


class JobMatchResponse(BaseModel):
    id: int
    user_id: int
    job_id: int
    score: int
    match_reasons: str | None
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True