from datetime import datetime

from typing import Literal

from pydantic import BaseModel, ConfigDict, field_validator


class CareerProfileCreate(BaseModel):
    professional_title: str | None = None
    skills: str | None = None
    years_of_experience: int = 0
    summary: str | None = None
    candidate_location: str | None = None
    preferred_work_type: str | None = None
    preferred_location: str | None = None
    minimum_salary: int | None = None
    maximum_salary: int | None = None
    salary_currency: str | None = None
    salary_period: Literal["month", "year"] | None = None

    @field_validator("salary_currency")
    @classmethod
    def validate_currency(cls, value: str | None) -> str | None:
        if value is None or not value.strip():
            return None

        value = value.strip().upper()

        if len(value) != 3 or not value.isalpha():
            raise ValueError(
                "Salary currency must be a 3-letter code such as USD"
            )

        return value


class CareerProfileResponse(BaseModel):
    id: int
    user_id: int
    professional_title: str | None
    years_of_experience: int
    summary: str | None
    skills: str | None
    candidate_location: str | None
    preferred_work_type: str | None
    preferred_location: str | None
    minimum_salary: int | None
    maximum_salary: int | None
    salary_currency: str | None
    salary_period: str | None
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)