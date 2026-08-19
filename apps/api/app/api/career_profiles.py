from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.db.database import get_db
from app.models.career_profile import CareerProfile
from app.models.user import User
from app.schemas.career_profile import (
    CareerProfileCreate,
    CareerProfileResponse,
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
        years_of_experience=profile_data.years_of_experience,
        summary=profile_data.summary,
        preferred_work_type=profile_data.preferred_work_type,
        preferred_location=profile_data.preferred_location,
        minimum_salary=profile_data.minimum_salary,
        maximum_salary=profile_data.maximum_salary,
    )

    db.add(profile)
    db.commit()
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
    profile.years_of_experience = profile_data.years_of_experience
    profile.summary = profile_data.summary
    profile.preferred_work_type = profile_data.preferred_work_type
    profile.preferred_location = profile_data.preferred_location
    profile.minimum_salary = profile_data.minimum_salary
    profile.maximum_salary = profile_data.maximum_salary

    db.commit()
    db.refresh(profile)

    return profile