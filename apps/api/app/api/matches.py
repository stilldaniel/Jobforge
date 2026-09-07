from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.db.database import get_db
from app.models.job import Job
from app.models.job_match import JobMatch
from app.schemas.job_match import MatchedJobResponse
from app.services.match_jobs import generate_job_matches


router = APIRouter(
    prefix="/matches",
    tags=["Matches"],
)


def serialize_match(match: JobMatch) -> dict:
    job = match.job

    return {
        "id": match.id,
        "user_id": match.user_id,
        "job_id": match.job_id,
        "score": match.score,
        "match_reasons": match.match_reasons,

        # Job information
        "title": job.title,
        "company": job.company,
        "description": job.description,
        "required_skills": job.required_skills,
        "required_experience": job.required_experience,
        "location": job.location,
        "remote_eligibility": job.remote_eligibility,
        "work_type": job.work_type,
        "salary_min": job.salary_min,
        "salary_max": job.salary_max,
        "application_url": job.application_url,

        "created_at": match.created_at,
        "updated_at": match.updated_at,
    }


@router.post(
    "/{user_id}/generate",
    response_model=list[MatchedJobResponse],
)
def generate_matches(
    user_id: int,
    db: Session = Depends(get_db),
):
    try:
        generate_job_matches(
            user_id=user_id,
            db=db,
        )

        matches = (
            db.query(JobMatch)
            .join(Job, Job.id == JobMatch.job_id)
            .filter(JobMatch.user_id == user_id)
            .order_by(JobMatch.score.desc())
            .all()
        )

        return [serialize_match(match) for match in matches]

    except ValueError as error:
        raise HTTPException(
            status_code=404,
            detail=str(error),
        )


@router.get(
    "/{user_id}",
    response_model=list[MatchedJobResponse],
)
def get_user_matches(
    user_id: int,
    db: Session = Depends(get_db),
):
    matches = (
        db.query(JobMatch)
        .join(Job, Job.id == JobMatch.job_id)
        .filter(JobMatch.user_id == user_id)
        .order_by(JobMatch.score.desc())
        .all()
    )

    if not matches:
        raise HTTPException(
            status_code=404,
            detail="No job matches found for this user",
        )

    return [serialize_match(match) for match in matches]

@router.post(
    "/{user_id}/notifications",
)
def create_match_notifications(
    user_id: int,
    db: Session = Depends(get_db),
):
    matches = (
        db.query(JobMatch)
        .filter(
            JobMatch.user_id == user_id
        )
        .all()
    )

    if not matches:
        raise HTTPException(
            status_code=404,
            detail="No job matches found for this user",
        )

    from app.services.notification_service import (
        create_notification_for_match,
    )

    created_notifications = []

    for match in matches:
        notification = create_notification_for_match(
            db=db,
            match=match,
        )

        if notification:
            created_notifications.append(
                notification
            )

    return {
        "message": "Notifications created",
        "notifications_created": len(
            created_notifications
        ),
        "notifications": [
            {
                "id": notification.id,
                "job_match_id": notification.job_match_id,
                "type": notification.notification_type,
                "status": notification.status,
                "title": notification.title,
                "message": notification.message,
            }
            for notification in created_notifications
        ],
    }