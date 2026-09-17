from app.job_sources.base import DiscoveredJob, JobSource
from app.job_sources.registry import get_job_sources
from app.services.job_monitor import monitor_jobs


class FakeJobSource(JobSource):
    def __init__(self, company: str):
        self.company = company

    def fetch_jobs(self) -> list[DiscoveredJob]:
        return [
            DiscoveredJob(
                title="Frontend Developer",
                company=self.company,
                description="Build modern web applications.",
                location="Lagos, Nigeria",
                work_type="remote",
                salary_min=3000,
                salary_max=4000,
                application_url=f"https://example.com/{self.company.lower()}",
                source="test",
                posted_at=None,
                remote_eligibility="Worldwide",
            )
        ]


class FailingJobSource(JobSource):
    def fetch_jobs(self) -> list[DiscoveredJob]:
        raise RuntimeError("API timeout")


def create_profile(db):
    from app.models.career_profile import CareerProfile

    profile = CareerProfile(
        user_id=1,
        professional_title="Frontend Developer",
        skills="React, Next.js, TypeScript, JavaScript",
        years_of_experience=5,
        summary="Frontend developer experienced in modern web applications.",
        candidate_location="Lagos, Nigeria",
        preferred_work_type="remote",
        preferred_location="Worldwide",
        minimum_salary=2500,
        maximum_salary=5000,
    )

    db.add(profile)
    db.flush()

    return profile


def test_default_registry_returns_mock_source():
    sources = get_job_sources()

    assert len(sources) == 1
    assert sources[0].__class__.__name__ == "MockJobSource"


def test_monitoring_accepts_injected_job_source(db):
    from app.models.job import Job
    from app.models.job_match import JobMatch
    from app.models.notification import Notification

    create_profile(db)

    source = FakeJobSource("Injected Test Company")

    result = monitor_jobs(
        db=db,
        sources=[source],
    )

    assert result["new_jobs"] == 1
    assert result["updated_jobs"] == 0
    assert result["matches_created"] == 1
    assert result["notifications_created"] == 1
    assert result["source_errors"] == []

    job = (
        db.query(Job)
        .filter(Job.company == "Injected Test Company")
        .first()
    )

    assert job is not None

    assert db.query(Job).count() == 1
    assert db.query(JobMatch).count() == 1
    assert db.query(Notification).count() == 1


def test_monitoring_accepts_multiple_injected_sources(db):
    from app.models.job import Job
    from app.models.job_match import JobMatch
    from app.models.notification import Notification

    create_profile(db)

    sources = [
        FakeJobSource("Source One"),
        FakeJobSource("Source Two"),
    ]

    result = monitor_jobs(
        db=db,
        sources=sources,
    )

    assert result["new_jobs"] == 2
    assert result["updated_jobs"] == 0
    assert result["matches_created"] == 2
    assert result["notifications_created"] == 2
    assert result["source_errors"] == []

    assert db.query(Job).count() == 2
    assert db.query(JobMatch).count() == 2
    assert db.query(Notification).count() == 2


def test_monitoring_continues_when_one_source_fails(db):
    from app.models.job import Job
    from app.models.job_match import JobMatch
    from app.models.notification import Notification

    create_profile(db)

    sources = [
        FakeJobSource("Working Source"),
        FailingJobSource(),
    ]

    result = monitor_jobs(
        db=db,
        sources=sources,
    )

    assert result["new_jobs"] == 1
    assert result["updated_jobs"] == 0
    assert result["matches_created"] == 1
    assert result["notifications_created"] == 1

    assert len(result["source_errors"]) == 1
    assert "FailingJobSource" in result["source_errors"][0]
    assert "API timeout" in result["source_errors"][0]

    assert db.query(Job).count() == 1
    assert db.query(JobMatch).count() == 1
    assert db.query(Notification).count() == 1


def test_monitoring_processes_other_sources_after_failure(db):
    from app.models.job import Job

    create_profile(db)

    sources = [
        FailingJobSource(),
        FakeJobSource("Source After Failure"),
    ]

    result = monitor_jobs(
        db=db,
        sources=sources,
    )

    assert result["new_jobs"] == 1
    assert result["matches_created"] == 1
    assert result["notifications_created"] == 1

    assert len(result["source_errors"]) == 1
    assert "FailingJobSource" in result["source_errors"][0]

    job = (
        db.query(Job)
        .filter(Job.company == "Source After Failure")
        .first()
    )

    assert job is not None


def test_monitoring_handles_all_sources_failing(db):
    create_profile(db)

    sources = [
        FailingJobSource(),
        FailingJobSource(),
    ]

    result = monitor_jobs(
        db=db,
        sources=sources,
    )

    assert result["jobs_found"] == 0
    assert result["new_jobs"] == 0
    assert result["updated_jobs"] == 0
    assert result["matches_created"] == 0
    assert result["notifications_created"] == 0

    assert len(result["source_errors"]) == 2
    assert all(
        "API timeout" in error
        for error in result["source_errors"]
    )