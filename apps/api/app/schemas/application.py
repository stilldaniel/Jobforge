from datetime import datetime

from pydantic import BaseModel, ConfigDict

from app.schemas.job import JobResponse


class ApplicationCreate(BaseModel):
    user_id: int
    job_id: int
    notes: str | None = None


class ApplicationUpdate(BaseModel):
    status: str | None = None
    notes: str | None = None


class ApplicationResponse(BaseModel):
    id: int
    user_id: int
    job_id: int
    status: str
    applied_at: datetime
    notes: str | None
    job: JobResponse

    model_config = ConfigDict(from_attributes=True)