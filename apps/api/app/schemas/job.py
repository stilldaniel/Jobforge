from datetime import datetime

from pydantic import BaseModel, ConfigDict


class JobCreate(BaseModel):
    title: str
    company: str
    description: str | None = None
    location: str | None = None
    work_type: str | None = None
    salary_min: int | None = None
    salary_max: int | None = None
    application_url: str
    source: str
    posted_at: datetime | None = None
    required_skills: str | None = None
    required_experience: int | None = None


class JobResponse(BaseModel):
    id: int
    title: str
    company: str
    description: str | None
    location: str | None
    work_type: str | None
    salary_min: int | None
    salary_max: int | None
    application_url: str
    source: str
    fingerprint: str
    posted_at: datetime | None
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)