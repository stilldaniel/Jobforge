from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.db.database import get_db
from app.models.job import Job
from app.schemas.job import JobCreate, JobResponse
from app.services.job_fingerprint import generate_job_fingerprint
from app.services.job_requirements import extract_requirements


router = APIRouter(
    prefix="/jobs",
    tags=["Jobs"],
)


def apply_job_data(
    job: Job,
    job_data: JobCreate,
) -> None:
    """
    Copy submitted fields onto a job, deriving the fingerprint
    and any requirements the caller did not provide.
    """

    requirements = extract_requirements(
        title=job_data.title,
        description=job_data.description,
    )

    job.title = job_data.title
    job.company = job_data.company
    job.description = job_data.description
    job.location = job_data.location
    job.work_type = job_data.work_type
    job.salary_min = job_data.salary_min
    job.salary_max = job_data.salary_max
    job.application_url = job_data.application_url
    job.source = job_data.source
    job.posted_at = job_data.posted_at
    job.required_skills = (
        job_data.required_skills
        if job_data.required_skills is not None
        else requirements["required_skills"]
    )
    job.required_experience = (
        job_data.required_experience
        if job_data.required_experience is not None
        else requirements["required_experience"]
    )
    job.fingerprint = job_fingerprint(job_data)


def job_fingerprint(job_data: JobCreate) -> str:
    return generate_job_fingerprint(
        title=job_data.title,
        company=job_data.company,
        application_url=job_data.application_url,
    )


def ensure_unique_fingerprint(
    db: Session,
    fingerprint: str,
    job_id: int | None = None,
) -> None:
    query = db.query(Job).filter(Job.fingerprint == fingerprint)

    if job_id is not None:
        query = query.filter(Job.id != job_id)

    if query.first():
        raise HTTPException(
            status_code=409,
            detail="A job with this title, company and URL already exists",
        )


@router.post("/", response_model=JobResponse)
def create_job(
    job_data: JobCreate,
    db: Session = Depends(get_db),
):
    ensure_unique_fingerprint(db, job_fingerprint(job_data))

    job = Job()
    apply_job_data(job, job_data)

    db.add(job)
    db.commit()
    db.refresh(job)

    return job


@router.get("/", response_model=list[JobResponse])
def get_jobs(
    db: Session = Depends(get_db),
):
    return db.query(Job).all()


@router.get("/{job_id}", response_model=JobResponse)
def get_job(
    job_id: int,
    db: Session = Depends(get_db),
):
    job = db.query(Job).filter(Job.id == job_id).first()

    if not job:
        raise HTTPException(
            status_code=404,
            detail="Job not found",
        )

    return job


@router.put("/{job_id}", response_model=JobResponse)
def update_job(
    job_id: int,
    job_data: JobCreate,
    db: Session = Depends(get_db),
):
    job = db.query(Job).filter(Job.id == job_id).first()

    if not job:
        raise HTTPException(
            status_code=404,
            detail="Job not found",
        )

    ensure_unique_fingerprint(
        db,
        job_fingerprint(job_data),
        job_id=job.id,
    )

    apply_job_data(job, job_data)

    db.commit()
    db.refresh(job)

    return job


@router.delete("/{job_id}")
def delete_job(
    job_id: int,
    db: Session = Depends(get_db),
):
    job = db.query(Job).filter(Job.id == job_id).first()

    if not job:
        raise HTTPException(
            status_code=404,
            detail="Job not found",
        )

    db.delete(job)
    db.commit()

    return {
        "message": "Job deleted successfully",
        "job_id": job_id,
    }