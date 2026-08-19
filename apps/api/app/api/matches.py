from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.db.database import get_db
from app.schemas.job_match import JobMatchResponse
from app.services.match_jobs import generate_job_matches
from app.models.job_match import JobMatch


router = APIRouter(
    prefix="/matches",
    tags=["Matches"],
)


@router.post(
    "/{user_id}/generate",
    response_model=list[JobMatchResponse],
)
def generate_matches(
    user_id: int,
    db: Session = Depends(get_db),
):
    try:
        matches = generate_job_matches(
            user_id=user_id,
            db=db,
        )

        return matches

    except ValueError as error:
        raise HTTPException(
            status_code=404,
            detail=str(error),
        )


@router.get(
    "/{user_id}",
    response_model=list[JobMatchResponse],
)
def get_user_matches(
    user_id: int,
    db: Session = Depends(get_db),
):
    matches = (
        db.query(JobMatch)
        .filter(JobMatch.user_id == user_id)
        .order_by(JobMatch.score.desc())
        .all()
    )

    if not matches:
        raise HTTPException(
            status_code=404,
            detail="No job matches found for this user",
        )

    return matches