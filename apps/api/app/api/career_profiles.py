import logging

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.db.database import get_db
from app.models.career_profile import CareerProfile
from app.models.user import User
from app.services.match_jobs import generate_job_matches
from app.schemas.career_profile import (
    CareerProfileCreate,
    CareerProfileResponse,
)


logger = logging.getLogger(__name__)


def rescore_matches(
    db: Session,
    user_id: int,
) -> None:
    """
    Re-score every job against the saved profile, so existing matches
    reflect the change straight away. No notifications are sent: a
    profile edit shouldn't email about jobs found earlier.
    """

    try:
        generate_job_matches(
            user_id=user_id,
            db=db,
        )
    except Exception:
        db.rollback()

        logger.exception(
            "Re-scoring matches failed after profile save | user_id=%s",
            user_id,
        )


router = APIRouter(
    prefix="/users/{user_id}/career-profile",
    tags=["Career Profile"],
)


@router.post("/", response_model=CareerProfileResponse)
def create_career_profile(
    user_id: int,
    profile_data: CareerProfileCreate,
    db: Session = Depends(get_db),
):
    user = db.query(User).filter(User.id == user_id).first()

    if not user:
        raise HTTPException(
            status_code=404,
            detail="User not found",
        )

    existing_profile = (
        db.query(CareerProfile)
        .filter(CareerProfile.user_id == user_id)
        .first()
    )

    if existing_profile:
        raise HTTPException(
            status_code=409,
            detail="Career profile already exists for this user",
        )

    profile = CareerProfile(
        user_id=user_id,
        professional_title=profile_data.professional_title,
        skills=profile_data.skills,
        years_of_experience=profile_data.years_of_experience,
        summary=profile_data.summary,
        preferred_work_type=profile_data.preferred_work_type,
        preferred_location=profile_data.preferred_location,
        minimum_salary=profile_data.minimum_salary,
        maximum_salary=profile_data.maximum_salary,
        salary_currency=profile_data.salary_currency,
        salary_period=profile_data.salary_period,
        candidate_location=profile_data.candidate_location,
    )

    db.add(profile)
    db.commit()
    db.refresh(profile)

    rescore_matches(db, user_id)
    db.refresh(profile)

    return profile


@router.get("/", response_model=CareerProfileResponse)
def get_career_profile(
    user_id: int,
    db: Session = Depends(get_db),
):
    profile = (
        db.query(CareerProfile)
        .filter(CareerProfile.user_id == user_id)
        .first()
    )

    if not profile:
        raise HTTPException(
            status_code=404,
            detail="Career profile not found",
        )

    return profile


@router.put("/", response_model=CareerProfileResponse)
def update_career_profile(
    user_id: int,
    profile_data: CareerProfileCreate,
    db: Session = Depends(get_db),
):
    profile = (
        db.query(CareerProfile)
        .filter(CareerProfile.user_id == user_id)
        .first()
    )

    if not profile:
        raise HTTPException(
            status_code=404,
            detail="Career profile not found",
        )

    profile.professional_title = profile_data.professional_title
    profile.skills = profile_data.skills
    profile.years_of_experience = profile_data.years_of_experience
    profile.summary = profile_data.summary
    profile.candidate_location = profile_data.candidate_location
    profile.preferred_work_type = profile_data.preferred_work_type
    profile.preferred_location = profile_data.preferred_location
    profile.minimum_salary = profile_data.minimum_salary
    profile.maximum_salary = profile_data.maximum_salary
    profile.salary_currency = profile_data.salary_currency
    profile.salary_period = profile_data.salary_period

    db.commit()
    db.refresh(profile)

    rescore_matches(db, user_id)
    db.refresh(profile)

    return profile