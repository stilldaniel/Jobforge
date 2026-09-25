from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session, joinedload

from app.db.database import get_db
from app.models.job import Job
from app.models.saved_job import SavedJob
from app.models.user import User
from app.schemas.saved_job import SavedJobCreate, SavedJobResponse


router = APIRouter(
    prefix="/saved-jobs",
    tags=["Saved Jobs"],
)


@router.post(
    "/",
    response_model=SavedJobResponse,
)
def save_job(
    saved_job_data: SavedJobCreate,
    db: Session = Depends(get_db),
):
    user = (
        db.query(User)
        .filter(User.id == saved_job_data.user_id)
        .first()
    )

    if not user:
        raise HTTPException(
            status_code=404,
            detail="User not found",
        )

    job = (
        db.query(Job)
        .filter(Job.id == saved_job_data.job_id)
        .first()
    )

    if not job:
        raise HTTPException(
            status_code=404,
            detail="Job not found",
        )

    existing_saved_job = (
        db.query(SavedJob)
        .filter(
            SavedJob.user_id == saved_job_data.user_id,
            SavedJob.job_id == saved_job_data.job_id,
        )
        .first()
    )

    if existing_saved_job:
        raise HTTPException(
            status_code=409,
            detail="Job is already saved",
        )

    saved_job = SavedJob(
        user_id=saved_job_data.user_id,
        job_id=saved_job_data.job_id,
    )

    db.add(saved_job)
    db.commit()
    db.refresh(saved_job)

    saved_job.job = job

    return saved_job


@router.get(
    "/{user_id}",
    response_model=list[SavedJobResponse],
)
def get_saved_jobs(
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

    saved_jobs = (
        db.query(SavedJob)
        .options(joinedload(SavedJob.job))
        .filter(SavedJob.user_id == user_id)
        .order_by(SavedJob.created_at.desc())
        .all()
    )

    return saved_jobs


@router.get(
    "/{user_id}/{job_id}",
    response_model=SavedJobResponse,
)
def get_saved_job(
    user_id: int,
    job_id: int,
    db: Session = Depends(get_db),
):
    saved_job = (
        db.query(SavedJob)
        .options(joinedload(SavedJob.job))
        .filter(
            SavedJob.user_id == user_id,
            SavedJob.job_id == job_id,
        )
        .first()
    )

    if not saved_job:
        raise HTTPException(
            status_code=404,
            detail="Saved job not found",
        )

    return saved_job


@router.delete(
    "/{user_id}/{job_id}",
)
def unsave_job(
    user_id: int,
    job_id: int,
    db: Session = Depends(get_db),
):
    saved_job = (
        db.query(SavedJob)
        .filter(
            SavedJob.user_id == user_id,
            SavedJob.job_id == job_id,
        )
        .first()
    )

    if not saved_job:
        raise HTTPException(
            status_code=404,
            detail="Saved job not found",
        )

    db.delete(saved_job)
    db.commit()

    return {
        "message": "Job removed from saved jobs",
        "user_id": user_id,
        "job_id": job_id,
    }