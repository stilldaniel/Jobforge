from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session, joinedload

from app.db.database import get_db
from app.models.application import Application
from app.models.job import Job
from app.models.user import User
from app.schemas.application import (
    ApplicationCreate,
    ApplicationResponse,
    ApplicationUpdate,
)


router = APIRouter(
    prefix="/applications",
    tags=["Applications"],
)


VALID_STATUSES = {
    "applied",
    "interview",
    "offer",
    "rejected",
    "withdrawn",
}


@router.post(
    "/",
    response_model=ApplicationResponse,
)
def create_application(
    application_data: ApplicationCreate,
    db: Session = Depends(get_db),
):
    user = (
        db.query(User)
        .filter(User.id == application_data.user_id)
        .first()
    )

    if not user:
        raise HTTPException(
            status_code=404,
            detail="User not found",
        )

    job = (
        db.query(Job)
        .filter(Job.id == application_data.job_id)
        .first()
    )

    if not job:
        raise HTTPException(
            status_code=404,
            detail="Job not found",
        )

    existing_application = (
        db.query(Application)
        .filter(
            Application.user_id == application_data.user_id,
            Application.job_id == application_data.job_id,
        )
        .first()
    )

    if existing_application:
        raise HTTPException(
            status_code=409,
            detail="Application already exists for this job",
        )

    application = Application(
        user_id=application_data.user_id,
        job_id=application_data.job_id,
        notes=application_data.notes,
    )

    db.add(application)
    db.commit()
    db.refresh(application)

    application.job = job

    return application


@router.get(
    "/{user_id}",
    response_model=list[ApplicationResponse],
)
def get_applications(
    user_id: int,
    db: Session = Depends(get_db),
):
    user = (
        db.query(User)
        .filter(User.id == user_id)
        .first()
    )

    if not user:
        raise HTTPException(
            status_code=404,
            detail="User not found",
        )

    applications = (
        db.query(Application)
        .options(joinedload(Application.job))
        .filter(Application.user_id == user_id)
        .order_by(Application.applied_at.desc())
        .all()
    )

    return applications


@router.get(
    "/{user_id}/{job_id}",
    response_model=ApplicationResponse,
)
def get_application(
    user_id: int,
    job_id: int,
    db: Session = Depends(get_db),
):
    application = (
        db.query(Application)
        .options(joinedload(Application.job))
        .filter(
            Application.user_id == user_id,
            Application.job_id == job_id,
        )
        .first()
    )

    if not application:
        raise HTTPException(
            status_code=404,
            detail="Application not found",
        )

    return application


@router.patch(
    "/{user_id}/{job_id}",
    response_model=ApplicationResponse,
)
def update_application(
    user_id: int,
    job_id: int,
    application_data: ApplicationUpdate,
    db: Session = Depends(get_db),
):
    application = (
        db.query(Application)
        .options(joinedload(Application.job))
        .filter(
            Application.user_id == user_id,
            Application.job_id == job_id,
        )
        .first()
    )

    if not application:
        raise HTTPException(
            status_code=404,
            detail="Application not found",
        )

    if application_data.status is not None:
        status = application_data.status.strip().lower()

        if status not in VALID_STATUSES:
            raise HTTPException(
                status_code=400,
                detail=(
                    "Invalid application status. "
                    "Valid statuses are: "
                    "applied, interview, offer, rejected, withdrawn."
                ),
            )

        application.status = status

    if application_data.notes is not None:
        application.notes = application_data.notes

    db.commit()
    db.refresh(application)

    return application


@router.delete(
    "/{user_id}/{job_id}",
)
def delete_application(
    user_id: int,
    job_id: int,
    db: Session = Depends(get_db),
):
    application = (
        db.query(Application)
        .filter(
            Application.user_id == user_id,
            Application.job_id == job_id,
        )
        .first()
    )

    if not application:
        raise HTTPException(
            status_code=404,
            detail="Application not found",
        )

    db.delete(application)
    db.commit()

    return {
        "message": "Application deleted",
        "user_id": user_id,
        "job_id": job_id,
    }