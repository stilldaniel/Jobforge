from datetime import datetime, timezone

from app.job_sources.base import DiscoveredJob, JobSource


class MockJobSource(JobSource):

    def fetch_jobs(self) -> list[DiscoveredJob]:
        return [
            DiscoveredJob(
                title="Senior Frontend Developer",
                company="TechFlow",
                description=(
                    "We are looking for a frontend developer "
                    "with experience in React and TypeScript."
                ),
                location="Remote",
                work_type="remote",
                salary_min=3000,
                salary_max=5000,
                application_url="https://example.com/jobs/frontend-developer",
                source="mock",
                posted_at=datetime.now(timezone.utc),
            ),
            DiscoveredJob(
                title="React Developer",
                company="CloudWorks",
                description=(
                    "Build modern web applications using React, "
                    "TypeScript and modern frontend technologies."
                ),
                location="Remote",
                work_type="remote",
                salary_min=2500,
                salary_max=4500,
                application_url="https://example.com/jobs/react-developer",
                source="mock",
                posted_at=datetime.now(timezone.utc),
            ),
        ]