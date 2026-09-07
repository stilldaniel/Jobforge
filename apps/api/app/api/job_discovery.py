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

    created_jobs, updated_jobs = ingest_jobs(
        db=db,
        source=source,
    )

    return {
        "message": "Job discovery completed",
        "jobs_found": len(created_jobs),
        "jobs_updated": len(updated_jobs),
        "jobs": created_jobs,
        "updated_jobs": updated_jobs,
    }