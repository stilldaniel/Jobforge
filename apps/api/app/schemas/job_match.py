from datetime import datetime

from pydantic import BaseModel


class MatchedJobResponse(BaseModel):
    id: int
    user_id: int
    job_id: int
    score: int
    match_reasons: str | None

    # Job information
    title: str
    company: str
    description: str | None
    required_skills: str | None
    required_experience: int | None
    location: str | None
    remote_eligibility: str | None
    work_type: str | None
    salary_min: int | None
    salary_max: int | None
    application_url: str

    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True