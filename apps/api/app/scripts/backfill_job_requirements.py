from app.db.database import SessionLocal
from app.models.job import Job
from app.services.job_requirements import extract_requirements


def backfill_job_requirements():
    db = SessionLocal()

    try:
        jobs = db.query(Job).all()

        updated = 0

        for job in jobs:
            requirements = extract_requirements(
                title=job.title,
                description=job.description,
            )

            job.required_skills = requirements["required_skills"]
            job.required_experience = requirements["required_experience"]

            updated += 1

        db.commit()

        print(f"Updated {updated} jobs.")

    finally:
        db.close()


if __name__ == "__main__":
    backfill_job_requirements()