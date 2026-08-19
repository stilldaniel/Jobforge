from datetime import datetime

from pydantic import BaseModel, ConfigDict


class CareerProfileCreate(BaseModel):
    professional_title: str | None = None
    years_of_experience: int = 0
    summary: str | None = None
    preferred_work_type: str | None = None
    preferred_location: str | None = None
    minimum_salary: int | None = None
    maximum_salary: int | None = None


class CareerProfileResponse(BaseModel):
    id: int
    user_id: int
    professional_title: str | None
    years_of_experience: int
    summary: str | None
    preferred_work_type: str | None
    preferred_location: str | None
    minimum_salary: int | None
    maximum_salary: int | None
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)