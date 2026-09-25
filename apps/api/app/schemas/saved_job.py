from datetime import datetime

from pydantic import BaseModel, ConfigDict

from app.schemas.job import JobResponse


class SavedJobCreate(BaseModel):
    user_id: int
    job_id: int


class SavedJobResponse(BaseModel):
    id: int
    user_id: int
    job_id: int
    created_at: datetime
    job: JobResponse

    model_config = ConfigDict(from_attributes=True)