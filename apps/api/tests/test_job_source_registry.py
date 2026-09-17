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


def test_default_registry_returns_mock_source():
    sources = get_job_sources()

    assert len(sources) == 1
    assert sources[0].__class__.__name__ == "MockJobSource"


def test_monitoring_accepts_injected_job_source(db):
    from app.models.career_profile import CareerProfile
    from app.models.job import Job
    from app.models.job_match import JobMatch
    from app.models.notification import Notification

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

    source = FakeJobSource("Injected Test Company")

    result = monitor_jobs(
        db=db,
        sources=[source],
    )

    assert result["new_jobs"] == 1
    assert result["updated_jobs"] == 0
    assert result["matches_created"] == 1
    assert result["notifications_created"] == 1

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
    from app.models.career_profile import CareerProfile
    from app.models.job import Job
    from app.models.job_match import JobMatch
    from app.models.notification import Notification

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

    assert db.query(Job).count() == 2
    assert db.query(JobMatch).count() == 2
    assert db.query(Notification).count() == 2