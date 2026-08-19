from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.db.database import get_db
from app.job_sources.mock import MockJobSource
from app.services.job_ingestion import ingest_jobs


router = APIRouter(
    prefix="/job-discovery",
    tags=["Job Discovery"],
)


@router.post("/run")
def run_job_discovery(
    db: Session = Depends(get_db),
):
    source = MockJobSource()

    jobs = ingest_jobs(
        db=db,
        source=source,
    )

    return {
        "message": "Job discovery completed",
        "jobs_found": len(jobs),
        "jobs": jobs,
    }